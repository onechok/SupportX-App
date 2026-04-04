from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QProgressBar, QTextEdit, QVBoxLayout, QWidget


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SupportX Updater")
    parser.add_argument("--app-dir", required=True)
    parser.add_argument("--entrypoint", required=True)
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--current-version", required=True)
    parser.add_argument("--target-version", required=True)
    parser.add_argument("--repo-owner", required=True)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--github-api-url", default="https://api.github.com")
    parser.add_argument("--asset-url", default="")
    parser.add_argument("--github-token", default="")
    parser.add_argument("--parent-pid", type=int, default=0)
    return parser.parse_args()


def is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False

    if platform.system() == "Windows":
        return _is_process_alive_windows(pid)

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        # Garde-fou: certaines versions Python/Windows remontent des erreurs internes
        # via os.kill; on ne doit pas casser l'updater pour autant.
        return False
    return True


def _is_process_alive_windows(pid: int) -> bool:
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process = kernel32.OpenProcess
    open_process.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    open_process.restype = ctypes.c_void_p

    get_exit_code_process = kernel32.GetExitCodeProcess
    get_exit_code_process.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
    get_exit_code_process.restype = ctypes.c_int

    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int

    handle = open_process(PROCESS_QUERY_LIMITED_INFORMATION, 0, int(pid))
    if not handle:
        return False

    try:
        exit_code = ctypes.c_uint32(0)
        if not get_exit_code_process(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == STILL_ACTIVE
    finally:
        close_handle(handle)


class UpdateWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__()
        self.args = args

    def run(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="supportx-updater-"))
        app_dir = Path(self.args.app_dir).resolve()
        entrypoint = Path(self.args.entrypoint).resolve()
        config_path = Path(self.args.config_path).resolve()
        archive_path = temp_dir / "update_payload"
        extracted_dir = temp_dir / "extracted"

        try:
            self.status.emit("Preparation de la mise a jour")
            self.log.emit("Attente de la fermeture de l'application principale...")
            for _ in range(80):
                if not is_process_alive(self.args.parent_pid):
                    break
                time.sleep(0.25)

            self.progress.emit(8)
            url = self.args.asset_url or self._fetch_release_asset_url()
            if not url:
                raise RuntimeError("Aucun package de release GitHub disponible.")

            archive_path = archive_path.with_name(f"update_payload{self._archive_suffix_for_url(url)}")

            self.status.emit("Telechargement du package")
            self._download_file(url, archive_path)
            self.progress.emit(45)

            self.status.emit("Extraction des fichiers")
            extract_root = self._extract_archive(archive_path, extracted_dir)
            self.progress.emit(66)

            self.status.emit("Application de la mise a jour")
            self._copy_release_content(extract_root, app_dir)
            self._update_config_version(config_path, self.args.target_version)
            self.progress.emit(90)

            self.status.emit("Redemarrage de SupportX")
            self._restart_app(app_dir, entrypoint)
            self.progress.emit(100)
            self.finished_ok.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _fetch_release_asset_url(self) -> str:
        api_url = (
            f"{self.args.github_api_url.rstrip('/')}/repos/"
            f"{self.args.repo_owner}/{self.args.repo_name}/releases/latest"
        )
        headers = {"Accept": "application/vnd.github+json"}
        if self.args.github_token:
            headers["Authorization"] = f"Bearer {self.args.github_token}"

        response = requests.get(api_url, timeout=20, headers=headers)
        response.raise_for_status()
        data = response.json()

        assets = data.get("assets") or []
        preferred_assets = []
        fallback_assets = []
        for asset in assets:
            name = (asset.get("name") or "").lower()
            url = asset.get("browser_download_url") or ""
            if not url:
                continue
            if not (name.endswith(".zip") or name.endswith(".tar.gz") or name.endswith(".tgz")):
                continue

            if "supportx" in name and "source" not in name:
                preferred_assets.append((name, url))
            else:
                fallback_assets.append((name, url))

        selected = preferred_assets[0] if preferred_assets else (fallback_assets[0] if fallback_assets else None)
        if selected:
            self.log.emit(f"Asset release selectionne: {selected[0]}")
            return selected[1]

        fallback = data.get("zipball_url", "")
        if fallback:
            self.log.emit("Aucun asset binaire: utilisation du zip source GitHub.")
        return fallback

    def _download_file(self, url: str, target: Path) -> None:
        headers = {"Accept": "application/octet-stream"}
        if self.args.github_token:
            headers["Authorization"] = f"Bearer {self.args.github_token}"

        with requests.get(url, stream=True, timeout=60, headers=headers) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", "0") or 0)
            downloaded = 0
            with open(target, "wb") as handle:
                for chunk in response.iter_content(chunk_size=32768):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = int(min(44, (downloaded / total_size) * 44))
                        self.progress.emit(8 + pct)

    def _extract_archive(self, archive_path: Path, extracted_dir: Path) -> Path:
        extracted_dir.mkdir(parents=True, exist_ok=True)
        suffix = archive_path.suffix.lower()
        name = archive_path.name.lower()

        if suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extracted_dir)
        elif suffix in {".gz", ".tgz"} or name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(extracted_dir)
        else:
            # GitHub zipball can be downloaded without explicit extension.
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extracted_dir)

        return self._resolve_project_root(extracted_dir)

    @staticmethod
    def _archive_suffix_for_url(url: str) -> str:
        path = urlparse(url).path.lower()
        if path.endswith(".tar.gz"):
            return ".tar.gz"
        if path.endswith(".tgz"):
            return ".tgz"
        if path.endswith(".zip"):
            return ".zip"
        return ".zip"

    @staticmethod
    def _resolve_project_root(extracted_dir: Path) -> Path:
        direct_launcher = extracted_dir / "launcher.py"
        direct_pkg = extracted_dir / "supportx_app"
        if direct_launcher.exists() and direct_pkg.is_dir():
            return extracted_dir

        for child in extracted_dir.iterdir():
            if not child.is_dir():
                continue
            if (child / "launcher.py").exists() and (child / "supportx_app").is_dir():
                return child

        raise RuntimeError("Archive invalide: structure du projet SupportX introuvable.")

    def _copy_release_content(self, source_root: Path, app_dir: Path) -> None:
        skip = {
            ".git",
            ".venv",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            "config.json",
        }
        for item in source_root.iterdir():
            if item.name in skip:
                continue
            destination = app_dir / item.name
            if item.is_dir():
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(item, destination)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destination)

    def _update_config_version(self, config_path: Path, version: str) -> None:
        if not config_path.exists():
            return
        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            data["app_version"] = version
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=4, ensure_ascii=False)
        except Exception as exc:
            self.log.emit(f"Info: version non ecrite dans config.json ({exc})")

    def _restart_app(self, app_dir: Path, entrypoint: Path) -> None:
        if not entrypoint.exists():
            raise RuntimeError(f"Entrypoint introuvable: {entrypoint}")
        subprocess.Popen([sys.executable, str(entrypoint)], cwd=str(app_dir), start_new_session=True)


class UpdaterWindow(QMainWindow):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__()
        self.worker = UpdateWorker(args)

        self.setWindowTitle("SupportX Updater")
        self.resize(620, 360)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.title = QLabel(f"Mise a jour {args.current_version} -> {args.target_version}")
        self.status_label = QLabel("Initialisation...")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addWidget(self.title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_box, 1)

        self.setCentralWidget(root)

        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.log.connect(self._append_log)
        self.worker.finished_ok.connect(self._on_success)
        self.worker.failed.connect(self._on_failure)
        self.worker.start()

    def _append_log(self, message: str) -> None:
        self.log_box.append(message)

    def _on_success(self) -> None:
        self.status_label.setText("Mise a jour terminee. Relance en cours...")
        self._append_log("Mise a jour appliquee avec succes.")
        QTimer.singleShot(900, QApplication.instance().quit)

    def _on_failure(self, message: str) -> None:
        self.status_label.setText("Echec de la mise a jour")
        self._append_log(f"Erreur: {message}")
        self.progress.setValue(0)


def main() -> int:
    args = parse_args()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = UpdaterWindow(args)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
