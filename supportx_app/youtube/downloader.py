from __future__ import annotations

import re
import shutil
import sys
from importlib.util import find_spec
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal


PROGRESS_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")


@dataclass
class DownloadTask:
    task_id: int
    url: str
    media_type: str
    quality: str
    allow_playlist: bool
    output_dir: str
    status: str = "queued"
    progress: float = 0.0
    message: str = "En attente"
    command_preview: str = ""
    lines: list[str] = field(default_factory=list)

    def as_payload(self) -> dict:
        return {
            "task_id": self.task_id,
            "url": self.url,
            "media_type": self.media_type,
            "quality": self.quality,
            "allow_playlist": self.allow_playlist,
            "output_dir": self.output_dir,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "command_preview": self.command_preview,
        }


class YouTubeDownloadManager(QObject):
    task_created = Signal(dict)
    task_updated = Signal(dict)
    task_removed = Signal(int)
    task_log = Signal(int, str)
    availability_changed = Signal(bool, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tasks: dict[int, DownloadTask] = {}
        self._queue: list[int] = []
        self._next_task_id = 1
        self._active_task_id: int | None = None
        self._cancel_requested = False
        self._process: QProcess | None = None
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        self._is_available, self._availability_message = self._resolve_runner()

    def _resolve_runner(self) -> tuple[bool, str]:
        if shutil.which("yt-dlp"):
            if self.has_ffmpeg():
                return True, "yt-dlp et ffmpeg detectes. Gestionnaire pret."
            return (
                True,
                "yt-dlp detecte, ffmpeg absent: MP3 indisponible et certaines operations MP4 seront limitees.",
            )

        if find_spec("yt_dlp") is not None:
            if self.has_ffmpeg():
                return True, "Module yt_dlp et ffmpeg detectes. Gestionnaire pret."
            return (
                True,
                "Module yt_dlp detecte, ffmpeg absent: MP3 indisponible et certaines operations MP4 seront limitees.",
            )
        return False, "yt-dlp introuvable. Installez la dependance pour activer cet onglet."

    def has_ffmpeg(self) -> bool:
        return bool(shutil.which("ffmpeg"))

    def validate_task_requirements(self, media_type: str) -> tuple[bool, str]:
        if media_type == "mp3" and not self.has_ffmpeg():
            return True, "ffmpeg absent: fallback audio direct active (extension source conservee)."
        return True, ""

    def get_availability(self) -> tuple[bool, str]:
        return self._is_available, self._availability_message

    def refresh_availability(self) -> None:
        self._is_available, self._availability_message = self._resolve_runner()
        self.availability_changed.emit(self._is_available, self._availability_message)

    def create_task(
        self,
        url: str,
        media_type: str,
        quality: str,
        allow_playlist: bool,
        output_dir: str,
        start_now: bool = True,
    ) -> int:
        cleaned_url = (url or "").strip()
        task = DownloadTask(
            task_id=self._next_task_id,
            url=cleaned_url,
            media_type=media_type,
            quality=quality,
            allow_playlist=allow_playlist,
            output_dir=output_dir,
        )
        self._next_task_id += 1

        self._tasks[task.task_id] = task
        self._queue.append(task.task_id)
        self.task_created.emit(task.as_payload())

        if start_now:
            self._start_next_if_idle()

        return task.task_id

    def cancel_task(self, task_id: int) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return

        if self._active_task_id == task_id and self._process is not None:
            self._cancel_requested = True
            self._process.kill()
            task.status = "cancelled"
            task.message = "Annulation demandee"
            self.task_updated.emit(task.as_payload())
            return

        if task_id in self._queue:
            self._queue = [item for item in self._queue if item != task_id]
            task.status = "cancelled"
            task.message = "Retire de la file"
            self.task_updated.emit(task.as_payload())

    def remove_task(self, task_id: int) -> None:
        if self._active_task_id == task_id:
            self.cancel_task(task_id)
            return

        self._tasks.pop(task_id, None)
        self._queue = [item for item in self._queue if item != task_id]
        self.task_removed.emit(task_id)

    def retry_task(self, task_id: int) -> int | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None

        return self.create_task(
            url=task.url,
            media_type=task.media_type,
            quality=task.quality,
            allow_playlist=task.allow_playlist,
            output_dir=task.output_dir,
            start_now=True,
        )

    def clear_finished(self) -> None:
        removable = [
            task_id
            for task_id, task in self._tasks.items()
            if task.status in {"done", "failed", "cancelled"} and task_id != self._active_task_id
        ]
        for task_id in removable:
            self._tasks.pop(task_id, None)
            self.task_removed.emit(task_id)

    def _start_next_if_idle(self) -> None:
        if not self._is_available or self._active_task_id is not None:
            return

        while self._queue:
            task_id = self._queue.pop(0)
            task = self._tasks.get(task_id)
            if task is None or task.status in {"cancelled", "done", "failed"}:
                continue
            self._start_task(task)
            break

    def _start_task(self, task: DownloadTask) -> None:
        task.status = "running"
        task.message = "Preparation du telechargement"
        task.progress = 0.0

        try:
            runner_program, runner_args = self._build_command(task)
        except ValueError as exc:
            task.status = "failed"
            task.message = str(exc)
            self.task_updated.emit(task.as_payload())
            self._start_next_if_idle()
            return
        task.command_preview = " ".join([runner_program] + runner_args)

        self._active_task_id = task.task_id
        self._cancel_requested = False
        self._stdout_buffer = ""
        self._stderr_buffer = ""

        self._process = QProcess(self)
        self._process.setProgram(runner_program)
        self._process.setArguments(runner_args)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)
        self._process.start()

        self.task_updated.emit(task.as_payload())

    def _build_command(self, task: DownloadTask) -> tuple[str, list[str]]:
        ffmpeg_available = self.has_ffmpeg()
        is_playlist_url = self._looks_like_playlist_url(task.url)

        if task.allow_playlist and is_playlist_url:
            output_template = str(
                Path(task.output_dir)
                / "%(playlist_title)s"
                / "%(playlist_index,playlist_autonumber)03d - %(title).180B - %(id)s.%(ext)s"
            )
        else:
            output_template = str(Path(task.output_dir) / "%(title).180B - %(id)s.%(ext)s")

        base_args = [
            "--newline",
            "--no-color",
            "--ignore-errors",
            "--no-overwrites",
            "--restrict-filenames",
            "-o",
            output_template,
        ]

        if ffmpeg_available:
            base_args.append("--embed-metadata")

        if task.allow_playlist:
            base_args.append("--yes-playlist")
        else:
            base_args.append("--no-playlist")

        if task.media_type == "mp3":
            quality_map = {
                "Best": "0",
                "High": "2",
                "Medium": "5",
                "Low": "7",
            }
            if ffmpeg_available:
                base_args.extend(
                    [
                        "-x",
                        "--audio-format",
                        "mp3",
                        "--audio-quality",
                        quality_map.get(task.quality, "0"),
                    ]
                )
            else:
                no_ffmpeg_audio_map = {
                    "Best": "bestaudio/best",
                    "High": "bestaudio[abr>=128]/bestaudio/best",
                    "Medium": "bestaudio[abr>=96]/bestaudio/best",
                    "Low": "bestaudio/best",
                }
                base_args.extend(["-f", no_ffmpeg_audio_map.get(task.quality, "bestaudio/best")])
        else:
            if ffmpeg_available:
                video_format_map = {
                    "Best": "bv*+ba/b",
                    "1080p": "bv*[height<=1080]+ba/b[height<=1080]",
                    "720p": "bv*[height<=720]+ba/b[height<=720]",
                    "480p": "bv*[height<=480]+ba/b[height<=480]",
                    "360p": "bv*[height<=360]+ba/b[height<=360]",
                }
                base_args.extend(
                    [
                        "-f",
                        video_format_map.get(task.quality, "bv*+ba/b"),
                        "--merge-output-format",
                        "mp4",
                    ]
                )
            else:
                # Sans ffmpeg, on evite les operations de fusion/post-traitement.
                no_ffmpeg_format_map = {
                    "Best": "best[ext=mp4]/best",
                    "1080p": "best[ext=mp4][height<=1080]/best[height<=1080]/best",
                    "720p": "best[ext=mp4][height<=720]/best[height<=720]/best",
                    "480p": "best[ext=mp4][height<=480]/best[height<=480]/best",
                    "360p": "best[ext=mp4][height<=360]/best[height<=360]/best",
                }
                base_args.extend(["-f", no_ffmpeg_format_map.get(task.quality, "best[ext=mp4]/best")])

        base_args.append(task.url)

        binary = shutil.which("yt-dlp")
        if binary:
            return binary, base_args
        return sys.executable, ["-m", "yt_dlp", *base_args]

    def _looks_like_playlist_url(self, url: str) -> bool:
        lowered = (url or "").lower()
        return "list=" in lowered or "/playlist" in lowered

    def _on_stdout(self) -> None:
        if self._process is None:
            return
        payload = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self._consume_output(payload, from_stderr=False)

    def _on_stderr(self) -> None:
        if self._process is None:
            return
        payload = self._process.readAllStandardError().data().decode("utf-8", errors="replace")
        self._consume_output(payload, from_stderr=True)

    def _consume_output(self, payload: str, from_stderr: bool) -> None:
        if self._active_task_id is None:
            return
        task = self._tasks.get(self._active_task_id)
        if task is None:
            return

        if from_stderr:
            self._stderr_buffer += payload
            lines = self._stderr_buffer.splitlines(keepends=True)
            if lines and not lines[-1].endswith("\n"):
                self._stderr_buffer = lines.pop()
            else:
                self._stderr_buffer = ""
        else:
            self._stdout_buffer += payload
            lines = self._stdout_buffer.splitlines(keepends=True)
            if lines and not lines[-1].endswith("\n"):
                self._stdout_buffer = lines.pop()
            else:
                self._stdout_buffer = ""

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            task.lines.append(cleaned)
            if len(task.lines) > 500:
                task.lines = task.lines[-500:]

            match = PROGRESS_RE.search(cleaned)
            if match:
                try:
                    task.progress = min(100.0, max(0.0, float(match.group(1))))
                    task.message = f"Telechargement en cours ({task.progress:.1f}%)"
                except ValueError:
                    pass
            elif cleaned.lower().startswith("[download]"):
                task.message = cleaned.replace("[download]", "").strip() or task.message
            elif "ffmpeg not found" in cleaned.lower():
                task.message = "ffmpeg manquant: fallback auto active sans conversion"
            elif "error" in cleaned.lower():
                task.message = cleaned

            self.task_log.emit(task.task_id, cleaned)

        self.task_updated.emit(task.as_payload())

    def _on_finished(self, exit_code: int, _exit_status) -> None:
        if self._active_task_id is None:
            return
        task = self._tasks.get(self._active_task_id)
        if task is None:
            return

        if self._cancel_requested:
            task.status = "cancelled"
            task.message = "Telechargement annule"
        elif exit_code == 0:
            task.status = "done"
            task.progress = 100.0
            task.message = "Telechargement termine"
        else:
            task.status = "failed"
            task.message = f"Echec du telechargement (code {exit_code})"

        self.task_updated.emit(task.as_payload())

        self._active_task_id = None
        self._process = None
        self._cancel_requested = False
        self._start_next_if_idle()
