"""Utilities for tagging media files to mimic Ray-Ban Meta hardware."""
from __future__ import annotations

import pathlib
import subprocess
from typing import Iterable, Sequence

DEFAULT_TAGS = {
    "Make": "Meta",
    "Model": "Ray-Ban Meta Smart Glasses",
    "Software": "Meta View App",
}

_BACKUP_SUFFIX = "_original"


class ExiftoolError(RuntimeError):
    """Raised when exiftool fails to process a file."""


def _build_command(
    path: pathlib.Path,
    *,
    exiftool_path: str,
    extra_args: Sequence[str] | None,
) -> list[str]:
    cmd: list[str] = [exiftool_path]
    for key, value in DEFAULT_TAGS.items():
        cmd.append(f"-{key}={value}")
    cmd.append("-overwrite_original")
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(str(path))
    return cmd


def _remove_backup_files(path: pathlib.Path) -> None:
    backup_path = path.parent / (path.name + _BACKUP_SUFFIX)
    if backup_path.exists():
        backup_path.unlink()
    legacy_name = path.stem + path.suffix + _BACKUP_SUFFIX
    legacy = path.parent / legacy_name
    if legacy.exists():
        legacy.unlink()


def tag_as_rayban(
    path: str | pathlib.Path,
    *,
    exiftool_path: str = "exiftool",
    extra_args: Iterable[str] | None = None,
) -> pathlib.Path:
    """Apply the Ray-Ban-style EXIF tags and return the updated path."""
    file_path = pathlib.Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    cmd = _build_command(file_path, exiftool_path=exiftool_path, extra_args=list(extra_args or ()))

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError as exc:
        raise ExiftoolError(
            "exiftool executable is missing. Install it and ensure it is on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ExiftoolError(exc.stderr.decode("utf-8", "ignore")) from exc

    _remove_backup_files(file_path)
    return file_path


__all__ = ["tag_as_rayban", "ExiftoolError", "DEFAULT_TAGS"]
