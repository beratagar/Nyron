"""
Hisse evrenini okuma / güncelleme.

- Öncelik: `data/bist500.txt` (önbellek) → XU500 (BIST 500) bileşenleri.
- Alternatif: `data/stocks.txt` (manuel liste).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

from config import FILES, UNIVERSE

logger = logging.getLogger(__name__)


def _ensure_is_suffix(symbol: str) -> str:
    s = (symbol or "").strip().upper()
    if not s:
        return ""
    return s if s.endswith(".IS") else f"{s}.IS"


def _parse_symbol_token(raw: str) -> str:
    s = (raw or "").strip().upper()
    if not s:
        return ""
    if s.endswith(".IS"):
        s = s[:-3]
    s = "".join(ch for ch in s if ch.isalnum())
    if not (4 <= len(s) <= 6):
        return ""
    return s


@dataclass(frozen=True)
class StockUniverseSource:
    name: str
    cache_path: Path
    meta_path: Path
    max_age: timedelta
    borsa_csv_url: str | None = None
    index_code: str | None = None


class StockReader:
    def __init__(self, base_dir: str | Path | None = None):
        root = Path(base_dir) if base_dir else Path(__file__).resolve().parents[2]
        self._root = root

        cache_rel = FILES.get("bist500_cache", "data/bist500.txt")
        meta_rel = FILES.get("bist500_meta", "data/bist500.meta.txt")
        max_age_h = float(UNIVERSE.get("cache_max_age_hours", 168))

        self._src = StockUniverseSource(
            name=str(UNIVERSE.get("name", "BIST 500 (XU500)")),
            cache_path=(root / cache_rel),
            meta_path=(root / meta_rel),
            max_age=timedelta(hours=max_age_h),
            borsa_csv_url=str(UNIVERSE.get("borsa_csv_url") or "") or None,
            index_code=str(UNIVERSE.get("index_code") or "") or None,
        )

        self._fallback_stocks_txt = root / "data" / "stocks.txt"

    def read_stocks(self) -> list[str]:
        if self._src.cache_path.exists():
            if self._is_cache_fresh():
                syms = self._read_symbol_file(self._src.cache_path)
                if syms:
                    return self._finalize(syms)
            else:
                if self._try_refresh_universe_cache():
                    syms = self._read_symbol_file(self._src.cache_path)
                    if syms:
                        return self._finalize(syms)
                syms = self._read_symbol_file(self._src.cache_path)
                if syms:
                    return self._finalize(syms)

        if self._fallback_stocks_txt.exists():
            syms = self._read_symbol_file(self._fallback_stocks_txt)
            if syms:
                return self._finalize(syms)

        logger.error("Hisse listesi bulunamadı. Beklenen: %s veya %s", self._src.cache_path, self._fallback_stocks_txt)
        return []

    def _finalize(self, clean_symbols: list[str]) -> list[str]:
        uniq = sorted({s for s in (clean_symbols or []) if s})
        return [_ensure_is_suffix(s) for s in uniq]

    def _read_symbol_file(self, path: Path) -> list[str]:
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError as exc:
            logger.warning("Dosya okunamadı: %s (%s)", path, exc)
            return []

        out: list[str] = []
        for line in raw:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            tok = _parse_symbol_token(s)
            if tok:
                out.append(tok)
        return out

    def _is_cache_fresh(self) -> bool:
        try:
            if self._src.meta_path.exists():
                txt = self._src.meta_path.read_text(encoding="utf-8", errors="ignore").strip()
                if txt:
                    ts = datetime.fromisoformat(txt)
                    return (datetime.now() - ts) <= self._src.max_age
        except Exception:
            pass
        try:
            mtime = datetime.fromtimestamp(self._src.cache_path.stat().st_mtime)
            return (datetime.now() - mtime) <= self._src.max_age
        except OSError:
            return False

    def _write_meta_now(self) -> None:
        try:
            self._src.meta_path.parent.mkdir(parents=True, exist_ok=True)
            self._src.meta_path.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
        except OSError:
            return

    def _try_refresh_universe_cache(self) -> bool:
        url = self._src.borsa_csv_url
        code = (self._src.index_code or "").strip().upper()
        if not url or not code:
            return False

        logger.info("Evren yenileniyor: %s (%s)", self._src.name, code)
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
        except Exception as exc:
            logger.warning("Evren CSV indirilemedi: %s", exc)
            return False

        text = r.text
        df = None
        for sep in (";", ",", "\t"):
            try:
                df = pd.read_csv(pd.io.common.StringIO(text), sep=sep)
                if df is not None and not df.empty and df.shape[1] >= 2:
                    break
            except Exception:
                df = None
        if df is None or df.empty:
            logger.warning("Evren CSV okunamadı (boş).")
            return False

        cols = {c.lower(): c for c in df.columns}
        idx_col = None
        for cand in ("endeks", "index", "endeks_kodu", "endeks kodu"):
            if cand in cols:
                idx_col = cols[cand]
                break
        sym_col = None
        for cand in ("kod", "code", "hisse", "symbol", "sembol"):
            if cand in cols:
                sym_col = cols[cand]
                break

        if idx_col is None or sym_col is None:
            idx_col = df.columns[0]
            sym_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        sub = df[df[idx_col].astype(str).str.upper().str.contains(code, na=False)]
        if sub.empty:
            logger.warning("Evren CSV içinde %s bulunamadı; cache güncellenmedi.", code)
            return False

        syms = []
        for v in sub[sym_col].tolist():
            tok = _parse_symbol_token(str(v))
            if tok:
                syms.append(tok)
        syms = sorted(set(syms))
        if not syms:
            logger.warning("Evren sembolleri çıkarılamadı; cache güncellenmedi.")
            return False

        try:
            self._src.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._src.cache_path.write_text("\n".join(syms) + "\n", encoding="utf-8")
            self._write_meta_now()
            logger.info("Evren cache güncellendi: %s (%s hisse)", self._src.cache_path, len(syms))
            return True
        except OSError as exc:
            logger.warning("Evren cache yazılamadı: %s", exc)
            return False

