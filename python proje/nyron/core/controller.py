# -*- coding: utf-8 -*-
"""Tarama sonuçları: filtreleme ve türetilmiş listeler (UI'dan bağımsız)."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import SCREEN
from nyron.core.text import format_signal_tr

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]  # proje kökü
SECTOR_FILE = BASE_DIR / "data" / "sectors.json"


def load_sector_map() -> dict:
    if not SECTOR_FILE.exists():
        logger.warning("Sektör dosyası yok: %s", SECTOR_FILE)
        return {}
    try:
        with SECTOR_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return {str(k).upper(): str(v) for k, v in data.items()}
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Sektör haritası okunamadı: %s", exc)
        return {}


SECTOR_MAP = load_sector_map()


def clean_symbol(symbol: str) -> str:
    return symbol.replace(".IS", "")


def signal_filter_from_combo(item_data) -> str:
    """QComboBox itemData veya 'Tümü' metni."""
    if item_data is None:
        return "Tümü"
    s = str(item_data)
    return s if s else "Tümü"


def parse_rsi_numeric(result: dict):
    r = result.get("rsi")
    if isinstance(r, (int, float)) and not pd.isna(r):
        return float(r)
    return None


def is_buy_opportunity_candidate(result: dict) -> bool:
    from config import SCORING

    if SCORING.get("opportunity_require_buy_signal", True) and result.get("signal") != "BUY":
        return False
    min_s = SCORING.get("opportunity_min_score", SCORING["buy_threshold"])
    if result["score"] < min_s:
        return False
    cap = SCORING.get("opportunity_max_rsi")
    if cap is None:
        return True
    rsi = parse_rsi_numeric(result)
    if rsi is not None and rsi > cap:
        return False
    return True


def has_volume_spike(symbol: str, all_data: dict) -> bool:
    ticker_full = f"{symbol}.IS" if not str(symbol).endswith(".IS") else symbol
    df = all_data.get(ticker_full)
    if df is None or len(df) < 30:
        return False
    current_vol = df["Volume"].iloc[-1]
    avg_vol = df["Volume"].tail(30).mean()
    if avg_vol <= 0:
        return False
    return (current_vol / avg_vol) > 1.5


def decorate_results(results: list, all_data: dict) -> None:
    from nyron.core.metrics import build_thesis_line

    for result in results:
        clean = clean_symbol(result["symbol"])
        result["sector"] = SECTOR_MAP.get(clean, "Bilinmiyor")
        result["volume_spike"] = has_volume_spike(result["symbol"], all_data)
        result["thesis"] = build_thesis_line(
            {
                "rs_20d": result.get("rs_20d"),
                "trend_label": result.get("trend_label"),
                "vol_ratio": result.get("vol_ratio"),
                "atr_pct": result.get("atr_pct"),
            },
            result.get("signal"),
            float(result.get("score") or 0),
        )


def parse_filter_float(value: str):
    try:
        s = (value or "").strip()
        return float(s) if s else None
    except ValueError:
        return None


def _text_matches_row(item: dict, q: str) -> bool:
    if not q:
        return True
    q_low = q.lower()
    sym = clean_symbol(str(item.get("symbol", "")))
    if q_low in sym.lower():
        return True
    sector = str(item.get("sector", "") or "")
    if q_low in sector.lower():
        return True
    thesis = str(item.get("thesis", "") or "")
    if q_low in thesis.lower():
        return True
    return False


def apply_filters(
    results: list,
    signal_filter: str,
    sector_filter: str,
    rsi_min: float | None,
    rsi_max: float | None,
    score_min: float | None,
    score_max: float | None,
    anomaly_only: bool,
    volume_only: bool,
    liquidity_only: bool = False,
    text_query: str | None = None,
    trend_filter: str | None = None,
    pct1d_min: float | None = None,
    pct1d_max: float | None = None,
    rs_outperform: bool = False,
    pct20_positive: bool = False,
    pct20_negative: bool = False,
    pct1d_positive: bool = False,
    pct1d_negative: bool = False,
    atr_high: bool = False,
    atr_low: bool = False,
    score_strong: bool = False,
    score_weak: bool = False,
) -> list:
    min_liq = float(SCREEN.get("min_vol_ratio_liquidity", 1.0))
    atr_hi = float(SCREEN.get("filter_atr_high_pct", 2.5))
    atr_lo = float(SCREEN.get("filter_atr_low_pct", 1.5))
    sc_hi = float(SCREEN.get("filter_score_strong", 70))
    sc_lo = float(SCREEN.get("filter_score_weak", 40))
    q = (text_query or "").strip()
    filtered = []
    for item in results:
        try:
            if signal_filter != "Tümü" and item.get("signal") != signal_filter:
                continue
            if anomaly_only and item.get("anomaly_color") != "yellow":
                continue
            if volume_only and not item.get("volume_spike"):
                continue
            if liquidity_only:
                vr = item.get("vol_ratio")
                if vr is None or vr < min_liq:
                    continue
            if sector_filter != "Tümü" and item.get("sector") != sector_filter:
                continue
            if trend_filter and trend_filter != "Tümü":
                if item.get("trend_label") != trend_filter:
                    continue
            if q and not _text_matches_row(item, q):
                continue
            p1 = item.get("pct_1d")
            if pct1d_min is not None:
                if p1 is None or p1 < pct1d_min:
                    continue
            if pct1d_max is not None:
                if p1 is None or p1 > pct1d_max:
                    continue
            rsi = item.get("rsi")
            if not isinstance(rsi, str):
                if rsi_min is not None and rsi < rsi_min:
                    continue
                if rsi_max is not None and rsi > rsi_max:
                    continue
            elif rsi_min is not None or rsi_max is not None:
                continue
            sc = item.get("score", 0)
            if score_min is not None and sc < score_min:
                continue
            if score_max is not None and sc > score_max:
                continue
            if rs_outperform:
                rsv = item.get("rs_20d")
                if rsv is None or rsv <= 0:
                    continue
            if pct20_positive:
                p20 = item.get("pct_20d")
                if p20 is None or p20 <= 0:
                    continue
            if pct20_negative:
                p20 = item.get("pct_20d")
                if p20 is None or p20 >= 0:
                    continue
            if pct1d_positive:
                if p1 is None or p1 <= 0:
                    continue
            if pct1d_negative:
                if p1 is None or p1 >= 0:
                    continue
            if atr_high:
                ap = item.get("atr_pct")
                if ap is None or ap < atr_hi:
                    continue
            if atr_low:
                ap = item.get("atr_pct")
                if ap is None or ap > atr_lo:
                    continue
            if score_strong and sc < sc_hi:
                continue
            if score_weak and sc > sc_lo:
                continue
            filtered.append(item)
        except (TypeError, KeyError) as exc:
            logger.debug("Filtre satırı atlandı: %s", exc)
            continue
    return filtered


def daily_pct_change(ticker_full: str, all_data: dict) -> float | None:
    df = all_data.get(ticker_full)
    if df is None or len(df) < 2:
        return None
    c = df["Close"]
    a, b = c.iloc[-1], c.iloc[-2]
    if pd.isna(a) or pd.isna(b) or b == 0:
        return None
    return float((a - b) / b * 100.0)


def volume_spike_entries(filtered_results: list, all_data: dict) -> list[tuple[dict, float]]:
    out = []
    for result in filtered_results:
        sym = result["symbol"]
        tf = sym if str(sym).endswith(".IS") else f"{sym}.IS"
        df = all_data.get(tf)
        if df is None or len(df) < 30:
            continue
        cur = df["Volume"].iloc[-1]
        avg = df["Volume"].tail(30).mean()
        if avg <= 0:
            continue
        ratio = float(cur / avg)
        if ratio > 1.5:
            out.append((result, ratio))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def resolve_ticker_full(ticker: str) -> str:
    return f"{ticker}.IS" if not str(ticker).endswith(".IS") else ticker


def suggested_scan_results_csv_filename() -> str:
    return f"tarama_sonuc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


def suggested_raw_ohlc_csv_filename(symbol_clean: str, trading_days: int, last_bar_date=None) -> str:
    s = str(symbol_clean).replace(".IS", "").strip().upper() or "HISSE"
    if last_bar_date is not None and hasattr(last_bar_date, "strftime"):
        dpart = last_bar_date.strftime("%d.%m.%Y")
    elif last_bar_date is not None:
        raw = str(last_bar_date)[:10]
        if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
            y, m, d = raw.split("-")
            dpart = f"{d}.{m}.{y}"
        else:
            dpart = datetime.now().strftime("%d.%m.%Y")
    else:
        dpart = datetime.now().strftime("%d.%m.%Y")
    _ = trading_days
    return f"{s}-{dpart}-HamVeri.csv"


def export_results_csv(rows: list[dict], path: str | Path | None = None, directory: str | None = None) -> Path | None:
    if path:
        out_path = Path(path)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("CSV klasörü oluşturulamadı: %s", exc)
            return None
    else:
        out_dir = Path(directory or SCREEN.get("export_dir", "outputs"))
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("CSV klasörü oluşturulamadı: %s", exc)
            return None
        name = f"tarama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        out_path = out_dir / name
    if not rows:
        return None
    keys = [
        "symbol",
        "sector",
        "price",
        "pct_1d",
        "pct_20d",
        "rs_20d",
        "vol_ratio",
        "atr_pct",
        "trend_label",
        "rsi",
        "macd",
        "score",
        "signal",
        "anomaly",
        "thesis",
    ]
    try:
        with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
            w = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in keys})
        logger.info("CSV kaydedildi: %s", out_path)
        return out_path
    except OSError as exc:
        logger.error("CSV yazılamadı: %s", exc)
        return None


def volume_ratio_for_symbol(ticker_full: str, all_data: dict) -> float | None:
    df = all_data.get(ticker_full)
    if df is None or len(df) < 30:
        return None
    avg = df["Volume"].tail(30).mean()
    if avg <= 0:
        return None
    return float(df["Volume"].iloc[-1] / avg)

