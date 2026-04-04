from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppConfig:
    theme: str = "system"
    auto_update: bool = True
    simulate_updates: bool = False
    app_name: str = "SupportX App"
    app_version: str = "1.0.0"
    supportx_url: str = "https://supportx.ch/"
    history_url: str = "https://supportx.ch/"
    update_server_url: str = "https://supportx.ch/updates/version.json"
    github_owner: str = "onechok"
    github_repo: str = "SupportX-App"
    github_repository_url: str = "https://github.com/onechok/SupportX-App"
    github_api_url: str = "https://api.github.com"
    github_token: str = ""

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        if not path.exists():
            config = cls()
            config.save(path)
            return config

        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)

        defaults = asdict(cls())
        changed = False
        for key, value in defaults.items():
            if key not in raw:
                raw[key] = value
                changed = True

        config = cls(**{k: raw[k] for k in defaults.keys()})
        if changed:
            config.save(path)
        return config

    def save(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(asdict(self), handle, indent=4, ensure_ascii=False)


def normalize_url(url: str, fallback: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return fallback
    if not cleaned.startswith(("http://", "https://")):
        return f"https://{cleaned}"
    return cleaned


def parse_version(version: str) -> list[int]:
    return [int(part) for part in version.split(".") if part.isdigit()]
