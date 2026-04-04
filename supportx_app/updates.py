from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

from .config import AppConfig, parse_version


@dataclass
class UpdateInfo:
    has_update: bool
    latest_version: str
    notes: str
    asset_url: str
    release_url: str


class UpdateService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def check(self) -> UpdateInfo:
        if self.config.simulate_updates:
            latest = "1.3.0"
            notes = "Version simulee: ameliorations visuelles et stabilite."
            return UpdateInfo(
                has_update=self._is_newer(latest),
                latest_version=latest,
                notes=notes,
                asset_url="",
                release_url="",
            )

        release = self._fetch_latest_github_release()
        latest = release.get("tag_name", "").lstrip("v") or self.config.app_version
        notes = release.get("body") or "Aucune note de mise a jour fournie."
        asset_url = self._select_release_asset_url(release)
        release_url = release.get("html_url", "")

        return UpdateInfo(
            has_update=self._is_newer(latest),
            latest_version=latest,
            notes=notes,
            asset_url=asset_url,
            release_url=release_url,
        )

    def launch_updater(
        self,
        update: UpdateInfo,
        app_dir: Path,
        config_path: Path,
        entrypoint_path: Path,
        parent_pid: int,
    ) -> tuple[bool, str]:
        if not update.has_update:
            return False, "Aucune mise a jour a appliquer."

        owner, repo = self._repo_coordinates()
        if not owner or not repo:
            return False, "Repository GitHub invalide pour Updater."

        command = [
            sys.executable,
            "-m",
            "supportx_app.updater.runner",
            "--app-dir",
            str(app_dir),
            "--entrypoint",
            str(entrypoint_path),
            "--config-path",
            str(config_path),
            "--current-version",
            self.config.app_version,
            "--target-version",
            update.latest_version,
            "--repo-owner",
            owner,
            "--repo-name",
            repo,
            "--github-api-url",
            self.config.github_api_url,
            "--parent-pid",
            str(parent_pid),
        ]

        if update.asset_url:
            command.extend(["--asset-url", update.asset_url])
        if self.config.github_token:
            command.extend(["--github-token", self.config.github_token])

        try:
            subprocess.Popen(command, cwd=str(app_dir), start_new_session=True)
        except Exception as exc:
            return False, f"Impossible de lancer Updater: {exc}"

        return True, "Updater lance"

    def _repo_coordinates(self) -> tuple[str, str]:
        owner = (self.config.github_owner or "").strip()
        repo = (self.config.github_repo or "").strip()

        parsed_owner, parsed_repo = self._parse_repo_from_url(self.config.github_repository_url)
        if parsed_owner and parsed_repo:
            return parsed_owner, parsed_repo
        return owner, repo

    @staticmethod
    def _parse_repo_from_url(url: str) -> tuple[str, str]:
        if not url:
            return "", ""
        parsed = urlparse(url.strip())
        if "github.com" not in parsed.netloc.lower():
            return "", ""

        parts = [segment for segment in parsed.path.split("/") if segment]
        if len(parts) < 2:
            return "", ""

        owner = parts[0].strip()
        repo = parts[1].strip()
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo

    def _fetch_latest_github_release(self) -> dict:
        owner, repo = self._repo_coordinates()
        if not owner or not repo:
            raise ValueError("Repository GitHub invalide. Configure github_repository_url ou github_owner/github_repo.")

        url = (
            f"{self.config.github_api_url.rstrip('/')}/repos/"
            f"{owner}/{repo}/releases/latest"
        )
        headers = {"Accept": "application/vnd.github+json"}
        if self.config.github_token:
            headers["Authorization"] = f"Bearer {self.config.github_token}"

        response = requests.get(url, timeout=20, headers=headers)
        response.raise_for_status()
        return response.json()

    def _select_release_asset_url(self, release: dict) -> str:
        assets = release.get("assets") or []
        for asset in assets:
            name = (asset.get("name") or "").lower()
            download_url = asset.get("browser_download_url") or ""
            if not download_url:
                continue
            if name.endswith(".zip") or name.endswith(".tar.gz") or name.endswith(".tgz"):
                return download_url

        return release.get("zipball_url", "")

    def _is_newer(self, latest: str) -> bool:
        return parse_version(latest) > parse_version(self.config.app_version)
