#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path


EXCLUDE_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SupportX release archives for GitHub Releases")
    parser.add_argument("--version", required=True, help="Semver without prefix v, e.g. 1.0.2")
    parser.add_argument("--repo-root", default=".", help="Project root")
    parser.add_argument("--output-dir", default="dist", help="Output directory")
    return parser.parse_args()


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_NAMES for part in path.parts)


def copy_project(src_root: Path, dst_root: Path) -> None:
    for item in src_root.iterdir():
        if item.name in EXCLUDE_NAMES:
            continue

        destination = dst_root / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                destination,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
            )
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def patch_config_version(config_path: Path, version: str) -> None:
    if not config_path.exists():
        return

    with open(config_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    data["app_version"] = version
    data["auto_update"] = True

    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4, ensure_ascii=False)


def create_zip(source_dir: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob("*"):
            if should_skip(path.relative_to(source_dir)):
                continue
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def create_tar_gz(source_dir: Path, archive_path: Path) -> None:
    with tarfile.open(archive_path, "w:gz") as tf:
        for path in source_dir.rglob("*"):
            if should_skip(path.relative_to(source_dir)):
                continue
            tf.add(path, arcname=path.relative_to(source_dir))


def main() -> int:
    args = parse_args()
    version = args.version.strip().lstrip("v")

    src_root = Path(args.repo_root).resolve()
    output_dir = (src_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="supportx-release-") as temp_dir:
        staging = Path(temp_dir) / f"supportx-app-v{version}"
        staging.mkdir(parents=True, exist_ok=True)

        copy_project(src_root, staging)
        patch_config_version(staging / "config/config.json", version)

        zip_path = output_dir / f"supportx-app-v{version}.zip"
        tar_path = output_dir / f"supportx-app-v{version}.tar.gz"

        create_zip(staging, zip_path)
        create_tar_gz(staging, tar_path)

        print(f"Built: {zip_path}")
        print(f"Built: {tar_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
