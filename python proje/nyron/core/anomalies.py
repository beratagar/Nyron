"""
Anomaly Detection Modülü - Uyumsuzluk Tespiti
"""

import logging

import numpy as np
import pandas as pd

from config import ANOMALY

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Hisse senedindeki anormal hareketleri tespit eder
    """

    def __init__(self):
        self.bb_breakout = ANOMALY["bb_breakout"]
        self.volume_spike = ANOMALY["volume_spike"]
        self.rsi_extreme = ANOMALY["rsi_extreme"]
        self.price_gap_percent = ANOMALY["price_gap_percent"]
        self.volume_drop = ANOMALY["volume_drop"]

    def detect(self, df: pd.DataFrame) -> dict:
        reasons: list[str] = []
        severities: list[str] = []
        details: dict = {}

        if self.bb_breakout and self._check_bb_breakout(df):
            reasons.append("BB Breakout")
            severities.append("medium")
            last = df.iloc[-1]
            details["bb_breakout"] = (
                f"Fiyat: {last['Close']:.2f}, Üst: {last.get('BB_Upper', 0):.2f}, Alt: {last.get('BB_Lower', 0):.2f}"
            )

        if self.volume_spike and self._check_volume_spike(df):
            reasons.append("Volume Spike")
            severities.append("low")
            last = df.iloc[-1]
            avg_vol = df["Volume"].tail(30).mean()
            ratio = last["Volume"] / avg_vol if avg_vol else 0
            details["volume_spike"] = f"Hacim: {int(last['Volume']):,}, Ort: {int(avg_vol):,}, Oran: {ratio:.2f}x"

        if self.rsi_extreme and self._check_rsi_extreme(df):
            reasons.append("RSI Extreme")
            severities.append("high")
            last = df.iloc[-1]
            rsi = last.get("RSI", 0)
            details["rsi_extreme"] = f"RSI: {rsi:.2f} ({'<10' if rsi < 10 else '>90'})"

        if self._check_price_gap(df):
            reasons.append("Price Gap")
            severities.append("medium")
            last = df.iloc[-1]
            prev = df.iloc[-2]
            gap = ((last["Open"] - prev["Close"]) / prev["Close"] * 100) if prev["Close"] else 0
            details["price_gap"] = f"Gap: {gap:+.2f}%"

        if self._check_volume_drop(df):
            reasons.append("Volume Drop")
            severities.append("low")
            last = df.iloc[-1]
            avg_vol = df["Volume"].tail(30).mean()
            ratio = last["Volume"] / avg_vol if avg_vol else 0
            details["volume_drop"] = f"Hacim: {int(last['Volume']):,}, Ort: {int(avg_vol):,}, Oran: {ratio:.2f}x"

        has_anomaly = bool(reasons)
        if has_anomaly:
            severity = "high" if "high" in severities else ("medium" if "medium" in severities else "low")
        else:
            severity = "none"

        return {
            "has_anomaly": has_anomaly,
            "reasons": reasons,
            "severity": severity,
            "color": "yellow" if has_anomaly else "green",
            "count": len(reasons),
            "details": details,
        }

    def _check_bb_breakout(self, df: pd.DataFrame) -> bool:
        latest = df.iloc[-1]
        close = latest["Close"]
        upper = latest.get("BB_Upper", np.nan)
        lower = latest.get("BB_Lower", np.nan)
        if pd.isna(upper) or pd.isna(lower):
            return False
        return close > upper or close < lower

    def _check_volume_spike(self, df: pd.DataFrame) -> bool:
        latest = df.iloc[-1]
        volume = latest["Volume"]
        volume_sma = latest.get("Volume_SMA", np.nan)
        if pd.isna(volume_sma) or volume_sma == 0:
            return False
        return (volume / volume_sma) > self.volume_spike

    def _check_rsi_extreme(self, df: pd.DataFrame) -> bool:
        latest = df.iloc[-1]
        rsi = latest.get("RSI", np.nan)
        if pd.isna(rsi):
            return False
        return rsi < 10 or rsi > 90

    def _check_price_gap(self, df: pd.DataFrame) -> bool:
        if len(df) < 2:
            return False
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        open_price = latest.get("Open", np.nan)
        prev_close = previous["Close"]
        if pd.isna(open_price) or not prev_close:
            return False
        gap_percent = abs(open_price - prev_close) / prev_close * 100
        return gap_percent > self.price_gap_percent

    def _check_volume_drop(self, df: pd.DataFrame) -> bool:
        latest = df.iloc[-1]
        volume = latest["Volume"]
        volume_sma = latest.get("Volume_SMA", np.nan)
        if pd.isna(volume_sma) or volume_sma == 0:
            return False
        return (volume / volume_sma) < self.volume_drop

