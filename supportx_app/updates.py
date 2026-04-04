from __future__ import annotations

import requests

from .config import parse_version


class UpdateService:
    def __init__(self, current_version: str, update_url: str, simulate: bool) -> None:
        self.current_version = current_version
        self.update_url = update_url
        self.simulate = simulate

    def check(self) -> tuple[bool, str, str]:
        if self.simulate:
            latest = "1.3.0"
            notes = "Version simulee: ameliorations visuelles et stabilite."
            return self._is_newer(latest), latest, notes

        response = requests.get(self.update_url, timeout=12)
        response.raise_for_status()
        data = response.json()

        latest = data.get("version", self.current_version)
        notes = data.get("notes", "Aucune note fournie.")
        return self._is_newer(latest), latest, notes

    def _is_newer(self, latest: str) -> bool:
        return parse_version(latest) > parse_version(self.current_version)
