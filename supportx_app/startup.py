from __future__ import annotations

import os
import plistlib
import shlex
import sys
from pathlib import Path


def _slug(app_name: str) -> str:
    return app_name.lower().replace(" ", "-")


def _linux_autostart_file(app_name: str) -> Path:
    slug = _slug(app_name)
    return Path.home() / ".config" / "autostart" / f"{slug}.desktop"


def _windows_startup_file(app_name: str) -> Path:
    slug = _slug(app_name)
    appdata = os.environ.get("APPDATA")
    if appdata:
        startup_root = Path(appdata)
    else:
        startup_root = Path.home() / "AppData" / "Roaming"
    startup_dir = startup_root / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return startup_dir / f"{slug}.cmd"


def _macos_launch_agent_file(app_name: str) -> Path:
    slug = app_name.lower().replace(" ", "-")
    return Path.home() / "Library" / "LaunchAgents" / f"ch.supportx.{slug}.plist"


def _desktop_entry(app_name: str, launcher_path: Path) -> str:
    exec_command = _exec_command(launcher_path)
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={app_name}\n"
        f"Exec={exec_command}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def _windows_script(launcher_path: Path) -> str:
    return "@echo off\n" + _exec_command(launcher_path, windows_quote=True) + "\n"


def _macos_plist(app_name: str, launcher_path: Path) -> dict:
    slug = _slug(app_name)
    command = _program_arguments(launcher_path)
    return {
        "Label": f"ch.supportx.{slug}",
        "ProgramArguments": command,
        "RunAtLoad": True,
        "KeepAlive": False,
    }


def _program_arguments(launcher_path: Path) -> list[str]:
    # If packaged (PyInstaller/cx_Freeze), relaunch the executable directly.
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, str(launcher_path)]


def _exec_command(launcher_path: Path, windows_quote: bool = False) -> str:
    args = _program_arguments(launcher_path)
    if windows_quote:
        return " ".join(f'\"{arg}\"' for arg in args)
    return " ".join(shlex.quote(arg) for arg in args)


def is_supported() -> bool:
    return sys.platform.startswith("linux") or sys.platform.startswith("win") or sys.platform == "darwin"


def set_startup(enabled: bool, app_name: str, app_dir: Path) -> tuple[bool, str]:
    if not is_supported():
        return False, "Demarrage automatique non supporte sur cette plateforme."

    launcher_path = app_dir / "launcher.py"
    platform_name = sys.platform

    if platform_name.startswith("linux"):
        target_file = _linux_autostart_file(app_name)
        if enabled:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(_desktop_entry(app_name, launcher_path), encoding="utf-8")
            return True, f"Demarrage active: {target_file}"

        if target_file.exists():
            target_file.unlink()
        return True, "Demarrage desactive"

    if platform_name.startswith("win"):
        target_file = _windows_startup_file(app_name)
        if enabled:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(_windows_script(launcher_path), encoding="utf-8")
            return True, f"Demarrage active: {target_file}"

        if target_file.exists():
            target_file.unlink()
        return True, "Demarrage desactive"

    if platform_name == "darwin":
        target_file = _macos_launch_agent_file(app_name)
        if enabled:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, "wb") as handle:
                plistlib.dump(_macos_plist(app_name, launcher_path), handle)
            return True, f"Demarrage active: {target_file}"

        if target_file.exists():
            target_file.unlink()
        return True, "Demarrage desactive"

    return False, "Demarrage automatique non supporte sur cette plateforme."
