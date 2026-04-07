"""
Yahoo Finance'tan veri çekme.
"""

from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

from config import DATA

logger = logging.getLogger(__name__)

_REQUIRED_OHLCV = ("Open", "High", "Low", "Close", "Volume")


class DataFetcher:
    def __init__(self):
        self.period = DATA["period"]
        self.interval = DATA["interval"]
        self.min_points = DATA["min_data_points"]
        # Optional process-level cache: avoids repeated downloads during the same run.
        self._memory_cache: dict[str, pd.DataFrame] = {}

    @staticmethod
    def _sanitize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        missing = [c for c in _REQUIRED_OHLCV if c not in df.columns]
        if missing:
            logger.warning("Eksik sütunlar: %s", missing)
            return pd.DataFrame()
        out = df.copy()
        out = out.ffill().bfill()
        out = out.dropna(subset=list(_REQUIRED_OHLCV))
        return out

    def fetch(self, symbols: list[str], progress_callback=None) -> dict[str, pd.DataFrame]:
        """Semboller için fiyat/hacim verisini (OHLCV) çek.

        Not: `yfinance.download(..., threads=True)` toplu indirme ile parça parça çalışır; her sembol için ayrı çağrı yapmaz.
        """
        results: dict[str, pd.DataFrame] = {}
        failed: list[str] = []

        if not symbols:
            return results

        # Normalize and keep order reasonably stable.
        uniq: list[str] = []
        seen: set[str] = set()
        for s in symbols:
            sym = str(s).strip().upper()
            if not sym or sym in seen:
                continue
            uniq.append(sym)
            seen.add(sym)

        total = len(uniq)
        done = 0

        def _emit_progress():
            if progress_callback:
                progress_callback(min(done, total), total)

        # Serve from in-memory cache first.
        remaining: list[str] = []
        for sym in uniq:
            cached = self._memory_cache.get(sym)
            if cached is not None and not cached.empty:
                results[sym] = cached
                done += 1
                _emit_progress()
            else:
                remaining.append(sym)

        if not remaining:
            return results

        # yfinance gets heavy with very long ticker lists; chunk to be safe.
        chunk_size = 60
        for start in range(0, len(remaining), chunk_size):
            batch = remaining[start : start + chunk_size]
            try:
                raw = yf.download(
                    tickers=" ".join(batch),
                    period=self.period,
                    interval=self.interval,
                    group_by="ticker",
                    auto_adjust=False,
                    threads=True,
                    progress=False,
                )
            except Exception as exc:
                logger.warning("Toplu indirme hatası (%s..%s): %s", start + 1, min(total, start + chunk_size), str(exc)[:120])
                raw = pd.DataFrame()

            # raw can be:
            # - empty
            # - columns: OHLCV (single ticker)
            # - columns: MultiIndex (ticker, field) for multiple tickers
            is_multi = isinstance(getattr(raw, "columns", None), pd.MultiIndex)

            for sym in batch:
                df = pd.DataFrame()
                try:
                    if raw is None or raw.empty:
                        df = pd.DataFrame()
                    elif is_multi:
                        # Some tickers may be missing in result.
                        if sym in raw.columns.get_level_values(0):
                            df = raw[sym].copy()
                        else:
                            df = pd.DataFrame()
                    else:
                        # Single ticker case: raw itself is OHLCV.
                        df = raw.copy()

                    df = self._sanitize_ohlcv(df)
                    if df.empty or len(df) < self.min_points:
                        logger.warning("  ❌ %s: Yetersiz veri (%s satır)", sym, len(df) if not df.empty else 0)
                        failed.append(sym)
                    else:
                        df.index.name = "Date"
                        results[sym] = df
                        self._memory_cache[sym] = df
                except Exception as e:
                    logger.warning("  ❌ %s: Hata - %s", sym, str(e)[:80])
                    failed.append(sym)
                finally:
                    done += 1
                    _emit_progress()

        logger.info("\n📊 Başarılı: %s, Başarısız: %s", len(results), len(failed))
        if failed:
            logger.warning("Başarısız: %s", failed)
        return results

