# -*- coding: utf-8 -*-
"""Nyron  logosu: PNG pencere simgesi ve sol üst logo."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from config import APP

APP_NAME = APP.get("name", "Nyron")

_LOGO_NAMES = (
    "nyronlogo.png",
    "nyron_logo.png",
    "logo.png",
    "brand.png",
    "app_icon.png",
    "icon.png",
    "app_icon.ico",
    "logo.ico",
    "nyron.ico",
    "nyron.png",
)


def _search_dirs() -> tuple[Path, ...]:
    pkg = Path(__file__).resolve().parent
    root = pkg.parent
    return (
        pkg / "resources",
        root / "assets",
        root / "resources",
    )


def _collect_images(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    ok = {".png", ".ico", ".jpg", ".jpeg", ".webp"}
    return [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in ok]


def _pick_fallback(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    stem_score = []
    for p in paths:
        s = p.stem.lower()
        score = 0
        for i, key in enumerate(("logo", "brand", "icon", "app")):
            if key in s:
                score += 10 - i
        stem_score.append((score, p.name.lower(), p))
    stem_score.sort(key=lambda x: (-x[0], x[1]))
    return stem_score[0][2]


def resolve_brand_logo_path() -> Path | None:
    for directory in _search_dirs():
        for name in _LOGO_NAMES:
            path = directory / name
            if path.is_file():
                return path
        picked = _pick_fallback(_collect_images(directory))
        if picked is not None:
            return picked
    return None


def try_load_brand_icon() -> QIcon | None:
    path = resolve_brand_logo_path()
    if path is None:
        return None
    pm = QPixmap(str(path))
    if pm.isNull():
        return None
    icon = QIcon()
    for s in (16, 20, 24, 32, 40, 48, 64, 96, 128, 256):
        icon.addPixmap(
            pm.scaled(
                s,
                s,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    return icon if not icon.isNull() else None


def scaled_brand_pixmap(path: Path, size: int = 52) -> QPixmap | None:
    pm = QPixmap(str(path))
    if pm.isNull():
        return None
    return pm.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
