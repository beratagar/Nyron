# -*- coding: utf-8 -*-
"""Temaya göre vektör tabanlı araç çubuğu / gezinme ikonları."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap

try:
    from PySide6.QtSvg import QSvgRenderer
except ImportError:
    QSvgRenderer = None


def _render_svg(svg_xml: str, size: int = 22) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    if QSvgRenderer is None:
        return pm
    r = QSvgRenderer(QByteArray(svg_xml.encode("utf-8")))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r.render(p)
    p.end()
    return pm


def _icon_from_svg(svg_xml: str) -> QIcon:
    ic = QIcon()
    for s in (18, 22, 28):
        ic.addPixmap(_render_svg(svg_xml, s))
    return ic


def icon_back(dark: bool) -> QIcon:
    c = "#e8eef4" if dark else "#0f172a"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>'''
    return _icon_from_svg(svg)


def icon_close(dark: bool) -> QIcon:
    c = "#e8eef4" if dark else "#0f172a"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>'''
    return _icon_from_svg(svg)


def icon_theme_to_light() -> QIcon:
    """Karanlık arka planda: aydınlığa geç — sıcak güneş."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#fcd34d" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4" fill="#fbbf24" stroke="#fde68a"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>'''
    return _icon_from_svg(svg)


def icon_theme_to_dark() -> QIcon:
    """Aydınlık arka planda: karanlığa geç — gece ayı."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" fill="#cbd5e1" stroke="#475569"/></svg>'''
    return _icon_from_svg(svg)
