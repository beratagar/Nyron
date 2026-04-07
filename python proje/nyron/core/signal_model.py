"""
Sinyal Üretimi Modülü - AL/SAT/TUT sinyalleri
"""

import logging

import numpy as np
import pandas as pd

from config import SCORING

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Buy/Sell sinyallerini ve skorları üretir

    Skor Ağırlıkları:
    - RSI: %25 (momentum)
    - MACD: %30 (trend)
    - Bollinger: %20 (volatilite)
    - Volume: %15 (katılım)
    - SMA: %10 (trend doğrulama)
    """

    def __init__(self):
        self.rsi_weight = SCORING["rsi_weight"]
        self.macd_weight = SCORING["macd_weight"]
        self.bollinger_weight = SCORING["bollinger_weight"]
        self.volume_weight = SCORING["volume_weight"]
        self.sma_weight = SCORING["sma_weight"]
        self.buy_threshold = SCORING["buy_threshold"]
        self.sell_threshold = SCORING["sell_threshold"]

    def generate_signal(self, indicators: dict) -> dict:
        details = {}

        rsi_score = self._rsi_score(indicators.get("rsi"))
        details["rsi_score"] = rsi_score

        macd_score = self._macd_score(
            indicators.get("macd"),
            indicators.get("macd_signal"),
            indicators.get("macd_hist"),
        )
        details["macd_score"] = macd_score

        bollinger_score = self._bollinger_score(
            indicators.get("close"),
            indicators.get("bb_upper"),
            indicators.get("bb_middle"),
            indicators.get("bb_lower"),
        )
        details["bollinger_score"] = bollinger_score

        volume_score = self._volume_score(
            indicators.get("volume"),
            indicators.get("volume_sma"),
        )
        details["volume_score"] = volume_score

        sma_score = self._sma_score(
            indicators.get("close"),
            indicators.get("sma_20"),
            indicators.get("sma_50"),
            indicators.get("sma_200"),
        )
        details["sma_score"] = sma_score

        total_score = (
            rsi_score * self.rsi_weight
            + macd_score * self.macd_weight
            + bollinger_score * self.bollinger_weight
            + volume_score * self.volume_weight
            + sma_score * self.sma_weight
        )

        if total_score >= self.buy_threshold:
            signal = "BUY"
            color = "green"
        elif total_score <= self.sell_threshold:
            signal = "SELL"
            color = "red"
        else:
            signal = "WAIT"
            color = "orange"

        return {"score": float(round(float(total_score), 2)), "signal": signal, "color": color, "details": details}

    def _rsi_score(self, rsi: float) -> float:
        if pd.isna(rsi):
            return 50
        if rsi < 30:
            return (30 - rsi) / 30 * 100
        if rsi <= 50:
            return float(max(35.0, min(88.0, 52.0 + (50.0 - rsi) * 1.15)))
        if rsi <= 70:
            return float(max(12.0, min(62.0, 72.0 - (rsi - 50.0) * 1.35)))
        return (100 - rsi) / 30 * 100

    def _macd_score(self, macd: float, signal: float, hist: float) -> float:
        if pd.isna(macd) or pd.isna(signal):
            return 50
        hist_ok = pd.notna(hist)
        if macd > signal and hist_ok and hist > 0:
            return 100
        if macd > signal:
            return 70 if hist_ok else 62
        if macd < signal and hist_ok and hist < 0:
            return 0
        if macd < signal:
            return 30
        return 45

    def _bollinger_score(self, close: float, upper: float, middle: float, lower: float) -> float:
        _ = middle
        if pd.isna(close) or pd.isna(upper) or pd.isna(lower):
            return 50
        if upper == lower:
            return 50
        position = (close - lower) / (upper - lower)
        position = max(0, min(1, position))
        return 100 * (1 - position)

    def _volume_score(self, volume: float, volume_sma: float) -> float:
        if pd.isna(volume) or pd.isna(volume_sma) or volume_sma == 0:
            return 50
        ratio = volume / volume_sma
        if ratio >= 1.5:
            return 100
        if ratio >= 1.0:
            return 70
        if ratio >= 0.5:
            return 50
        return 30

    def _sma_score(self, close: float, sma_20: float, sma_50: float, sma_200: float) -> float:
        if pd.isna(close) or pd.isna(sma_20) or pd.isna(sma_50) or pd.isna(sma_200):
            return 50
        if sma_200 < sma_50 < sma_20:
            return 100
        if sma_20 > sma_50:
            return 70
        if close > sma_200:
            return 50
        return 30

