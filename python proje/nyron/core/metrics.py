# -*- coding: utf-8 -*-
"""Hisse başına türetilmiş metrikler: getiri, ATR%, hacim, trend, göreli güç."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from config import SCORING
from nyron.core.text import format_signal_tr

logger = logging.getLogger(__name__)


def _pct_over_bars(close: pd.Series, bars: int) -> float | None:
    if close is None or len(close) < bars + 1:
        return None
    a, b = float(close.iloc[-1]), float(close.iloc[-(bars + 1)])
    if pd.isna(a) or pd.isna(b) or b == 0:
        return None
    return (a - b) / b * 100.0


def _trend_label_tr(df: pd.DataFrame) -> str:
    try:
        last = df.iloc[-1]
        c = last.get("Close")
        s20 = last.get("SMA_20")
        s50 = last.get("SMA_50")
        s200 = last.get("SMA_200")
        if any(pd.isna(x) for x in (c, s20, s50, s200)):
            return "—"
        if s20 > s50 > s200 and c > s20:
            return "Güçlü yükseliş"
        if s20 > s50 and c > s50:
            return "Yükseliş"
        if s20 < s50 < s200 and c < s20:
            return "Düşüş baskısı"
        if s20 < s50:
            return "Zayıf / düzeltme"
        if c > s200:
            return "Uzun vade üstü"
        return "Yatay / karışık"
    except Exception:
        return "—"


def _risk_vol_tr(atr_pct: float | None) -> str:
    if atr_pct is None or pd.isna(atr_pct):
        return "—"
    if atr_pct < 1.4:
        return "Düşük vol."
    if atr_pct <= 3.0:
        return "Normal vol."
    return "Yüksek vol."


def compute_equity_metrics(df: pd.DataFrame, benchmark_20d_pct: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "pct_1d": None,
        "pct_5d": None,
        "pct_20d": None,
        "pct_60d": None,
        "atr_pct": None,
        "vol_ratio": None,
        "trend_label": "—",
        "rs_20d": None,
        "risk_volatility": "—",
        "thesis": "",
    }
    if df is None or df.empty or "Close" not in df.columns:
        return out

    close = df["Close"]
    out["pct_1d"] = _pct_over_bars(close, 1)
    out["pct_5d"] = _pct_over_bars(close, 5)
    out["pct_20d"] = _pct_over_bars(close, 20)
    out["pct_60d"] = _pct_over_bars(close, 60)

    last = df.iloc[-1]
    atr = last.get("ATR")
    pc = last.get("Close")
    if pd.notna(atr) and pd.notna(pc) and float(pc) > 0:
        out["atr_pct"] = round(float(atr) / float(pc) * 100.0, 2)

    vs = last.get("Volume_SMA")
    vol = last.get("Volume")
    if pd.notna(vs) and pd.notna(vol) and float(vs) > 0:
        out["vol_ratio"] = round(float(vol) / float(vs), 2)

    out["trend_label"] = _trend_label_tr(df)
    out["risk_volatility"] = _risk_vol_tr(out["atr_pct"])

    s20 = out["pct_20d"]
    if s20 is not None and benchmark_20d_pct is not None:
        out["rs_20d"] = round(s20 - benchmark_20d_pct, 2)

    return out


def build_thesis_line(metrics: dict, signal: str | None = None, score: float | None = None) -> str:
    parts: list[str] = []
    if signal is not None and score is not None:
        try:
            sc = float(score)
        except (TypeError, ValueError):
            sc = 0.0
        parts.append(f"{format_signal_tr(signal, sc)} (skor {sc:.0f})")

    rs = metrics.get("rs_20d")
    if rs is not None:
        if rs >= 3:
            parts.append(f"BIST 100’den +{rs:.1f} pp güçlü")
        elif rs <= -3:
            parts.append(f"BIST 100’e göre {rs:.1f} pp geride")
        else:
            parts.append(f"BIST 100’e yakın ({rs:+.1f} pp)")

    tr = metrics.get("trend_label")
    if tr and str(tr).strip() not in ("", "—"):
        parts.append(str(tr).strip())

    vr = metrics.get("vol_ratio")
    if vr is not None and vr >= 1.4:
        parts.append(f"hacim ×{vr:.1f}")

    atrp = metrics.get("atr_pct")
    if atrp is not None and atrp >= 3:
        parts.append("yüksek oynaklık")

    return " · ".join(parts) if parts else "—"


def build_opportunity_rationale(result: dict) -> str:
    lines: list[str] = []
    lines.append(f"Sinyal: {format_signal_tr(result.get('signal'), result.get('score'))}")
    lines.append(f"Skor: {result.get('score', 0):.1f}")
    rsi = result.get("rsi")
    if isinstance(rsi, (int, float)) and not pd.isna(rsi):
        lines.append(f"RSI: {rsi:.1f}")
    rs = result.get("rs_20d")
    if rs is not None:
        lines.append(f"~20 iş günü göreli güç (BIST 100): {rs:+.2f} pp")
    if result.get("vol_ratio") is not None:
        lines.append(f"Hacim / 30g ort: {result['vol_ratio']:.2f}×")
    if result.get("pct_20d") is not None:
        lines.append(f"20 günlük getiri: {result['pct_20d']:+.2f}%")
    if result.get("risk_volatility"):
        lines.append(f"Risk (ATR): {result['risk_volatility']}")
    macd = result.get("macd")
    if macd == "↑":
        lines.append("MACD histogram pozitif eğilim")
    if result.get("anomaly_color") == "yellow":
        lines.append("Uyarı: teknik uyumsuzluk işareti")
    return " | ".join(lines) if lines else "—"


def build_opportunity_why_for_user(result: dict) -> str:
    sym = str(result.get("symbol") or "Hisse").strip() or "Hisse"
    min_s = float(SCORING.get("opportunity_min_score", 68))
    max_r = float(SCORING.get("opportunity_max_rsi", 73))
    require_buy = bool(SCORING.get("opportunity_require_buy_signal", True))
    sig = str(result.get("signal") or "—")
    sc = float(result.get("score") or 0)

    blok: list[str] = []
    sig_tr = format_signal_tr(sig, sc)
    if require_buy and sig == "BUY":
        blok.append(
            f"{sym} bu listede; model «al» yönünde ({sig_tr}) ve teknik skor {sc:.1f}, asgari eşiğin ({min_s:.0f}) üzerinde."
        )
    else:
        blok.append(f"{sym} için skor {sc:.1f}, sinyal {sig_tr}.")

    rsi = result.get("rsi")
    if isinstance(rsi, (int, float)) and not pd.isna(rsi):
        blok.append(
            f"RSI {rsi:.1f}: aşırı alım riskini sınırlamak için RSI üst sınırı {max_r:.0f} kullanılır; bu hisse bu sınırın altında."
        )

    rs = result.get("rs_20d")
    if rs is not None:
        if rs >= 2:
            blok.append(f"~20 iş günü göreli güç: endekse göre +{rs:.2f} puan (güçlü).")
        elif rs <= -2:
            blok.append(f"~20 iş günü göreli güç: endekse göre {rs:+.2f} puan (zayıf).")
        else:
            blok.append(f"~20 iş günü göreli güç: {rs:+.2f} puan (yakın).")

    p20 = result.get("pct_20d")
    if p20 is not None:
        blok.append(f"Son 20 işlem günü fiyat değişimi {p20:+.2f}%.")

    vr = result.get("vol_ratio")
    if vr is not None and vr >= 1.15:
        blok.append(f"Son gün hacmi 30g ortalamanın {vr:.2f} katı.")

    tr = result.get("trend_label")
    if tr and str(tr).strip() not in ("", "—"):
        blok.append(f"Trend özeti: {tr}.")

    thesis = (result.get("thesis") or "").strip()
    if thesis:
        blok.append(f"Tarama özeti: {thesis}")

    blok.append("Bilgi amaçlıdır; yatırım tavsiyesi değildir.")
    return "\n\n".join(blok)


def fetch_benchmark_20d_return(ticker: str, period: str = "6mo", interval: str = "1d") -> float | None:
    try:
        import yfinance as yf

        h = yf.Ticker(ticker).history(period=period, interval=interval)
        if h is None or h.empty or "Close" not in h.columns:
            return None
        c = h["Close"].dropna()
        return _pct_over_bars(c, 20)
    except Exception as exc:
        logger.warning("Benchmark verisi alınamadı (%s): %s", ticker, exc)
        return None

