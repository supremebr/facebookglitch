"""Minimal drop-in replacement for the removed stdlib imghdr module.

telegram.InputFile still imports imghdr on Python 3.13, so we ship the
small subset we need (what() with a few detectors) alongside the bot.
"""
from __future__ import annotations

from typing import Callable, Iterable, Union

Detector = Callable[[bytes], Union[str, None]]

_DETECTORS: list[Detector] = []


def register(detector: Detector) -> Detector:
    _DETECTORS.append(detector)
    return detector


def what(file, h: bytes | None = None) -> Union[str, None]:
    header = h if h is not None else _read_header(file)
    for detector in _DETECTORS:
        match = detector(header)
        if match:
            return match
    return None


def _read_header(file, length: int = 32) -> bytes:
    if hasattr(file, "read"):
        pos = file.tell()
        chunk = file.read(length)
        file.seek(pos)
        return chunk or b""
    with open(file, "rb") as fh:
        return fh.read(length)


@register
def _detect_jpeg(header: bytes) -> Union[str, None]:
    return "jpeg" if header.startswith(b"\xff\xd8\xff") else None


@register
def _detect_png(header: bytes) -> Union[str, None]:
    return "png" if header.startswith(b"\x89PNG\r\n\x1a\n") else None


@register
def _detect_gif(header: bytes) -> Union[str, None]:
    return "gif" if header.startswith((b"GIF87a", b"GIF89a")) else None


@register
def _detect_bmp(header: bytes) -> Union[str, None]:
    return "bmp" if header.startswith(b"BM") else None


@register
def _detect_tiff(header: bytes) -> Union[str, None]:
    start = header[:4]
    return "tiff" if start in (b"II*\x00", b"MM\x00*") else None


@register
def _detect_webp(header: bytes) -> Union[str, None]:
    return "webp" if header.startswith(b"RIFF") and header[8:12] == b"WEBP" else None
