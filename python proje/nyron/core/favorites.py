from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    # nyron/core/favorites.py -> nyron/core -> nyron -> project root
    return Path(__file__).resolve().parents[2]


@dataclass
class FavoritesStore:
    """Basit kalıcı favoriler deposu (temiz semboller).

    `data/favorites.json` içinde `ASELS` gibi semboller saklanır ('.IS' olmadan).
    """

    path: Path | None = None

    def __post_init__(self) -> None:
        if self.path is None:
            self.path = _project_root() / "data" / "favorites.json"

    def load(self) -> set[str]:
        p = Path(self.path)
        if not p.exists():
            return set()
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return set()
        if isinstance(raw, dict):
            raw = raw.get("favorites", [])
        if not isinstance(raw, list):
            return set()
        out: set[str] = set()
        for v in raw:
            s = str(v).strip().upper()
            if not s:
                continue
            if s.endswith(".IS"):
                s = s[:-3]
            s = "".join(ch for ch in s if ch.isalnum())
            if 2 <= len(s) <= 10:
                out.add(s)
        return out

    def save(self, favorites: set[str]) -> None:
        p = Path(self.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {"favorites": sorted({str(s).strip().upper() for s in favorites if str(s).strip()})}
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(p)

    def is_favorite(self, symbol_clean: str) -> bool:
        s = (symbol_clean or "").strip().upper().replace(".IS", "")
        if not s:
            return False
        fav = self.load()
        return s in fav

    def set_favorite(self, symbol_clean: str, enabled: bool) -> bool:
        s = (symbol_clean or "").strip().upper().replace(".IS", "")
        if not s:
            return False
        fav = self.load()
        changed = False
        if enabled:
            if s not in fav:
                fav.add(s)
                changed = True
        else:
            if s in fav:
                fav.remove(s)
                changed = True
        if changed:
            self.save(fav)
        return enabled

    def toggle(self, symbol_clean: str) -> bool:
        s = (symbol_clean or "").strip().upper().replace(".IS", "")
        if not s:
            return False
        fav = self.load()
        enabled = s not in fav
        if enabled:
            fav.add(s)
        else:
            fav.remove(s)
        self.save(fav)
        return enabled

