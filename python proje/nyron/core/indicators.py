"""
Teknik gösterge gösterge hesapları (günlük OHLCV).

Kontrol / tutarlılık:
- RSI: Wilder yumuşatması (ewm com=period-1); düz piyasada ~50.
- MACD: kapanış EMA farkı; sinyal çizgisi MACD üzerinde EMA; histogram farkı.
- Bollinger: orta bant = SMA(bb_period); üst/alt = ± bb_std × rolling std (ddof=0).
- ATR: true range üzerinde rolling ortalama (min_periods=period).
- Stokastik / Williams %R: (high−low)=0 bölgelerinde güvenli bölme (NaN).
- CCI: tipik fiyat MAD=0 iken NaN.
- ROC: payda (gecikmeli kapanış) 0 ise NaN.
- Momentum: Close.diff(10) — ek gösterge; sinyal ağırlıkları config’te.
"""

import logging

import numpy as np
import pandas as pd

from config import INDICATORS

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """Tüm teknik indikatorları hesaplar"""

    def __init__(self):
        self.rsi_period = INDICATORS["rsi_period"]
        self.macd_fast = INDICATORS["macd_fast"]
        self.macd_slow = INDICATORS["macd_slow"]
        self.macd_signal = INDICATORS["macd_signal"]
        self.bb_period = INDICATORS["bb_period"]
        self.bb_std = INDICATORS["bb_std"]
        self.sma_periods = INDICATORS["sma_periods"]
        self.volume_lookback = INDICATORS["volume_lookback"]

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["RSI"] = self.calculate_rsi(df)

        macd, signal, hist = self.calculate_macd(df)
        df["MACD"] = macd
        df["MACD_Signal"] = signal
        df["MACD_Hist"] = hist

        upper, middle, lower = self.calculate_bollinger(df)
        df["BB_Upper"] = upper
        df["BB_Middle"] = middle
        df["BB_Lower"] = lower

        for period in self.sma_periods:
            df[f"SMA_{period}"] = df["Close"].rolling(window=period, min_periods=period).mean()

        df["Volume_SMA"] = df["Volume"].rolling(
            window=self.volume_lookback, min_periods=self.volume_lookback
        ).mean()

        df["Stochastic"] = self._calculate_stochastic(df)
        df["CCI"] = self._calculate_cci(df)
        df["ATR"] = self._calculate_atr(df)
        df["Momentum"] = df["Close"].diff(10)
        df["ROC"] = self._calculate_roc(df)
        df["Williams_R"] = self._calculate_williams_r(df)

        return df

    def calculate_core(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scan-time indicator set (fast).

        Only computes columns needed by:
        - scoring (`SignalGenerator`)
        - anomaly detection (`AnomalyDetector`)
        - metrics (`compute_equity_metrics`)
        - basic UI table fields

        Full indicator suite is computed lazily when opening detail view.
        """
        if df is None or df.empty:
            return df
        out = df.copy()

        # RSI
        out["RSI"] = self.calculate_rsi(out)

        # MACD (+ signal, histogram)
        macd, signal, hist = self.calculate_macd(out)
        out["MACD"] = macd
        out["MACD_Signal"] = signal
        out["MACD_Hist"] = hist

        # Bollinger Bands
        upper, middle, lower = self.calculate_bollinger(out)
        out["BB_Upper"] = upper
        out["BB_Middle"] = middle
        out["BB_Lower"] = lower

        # SMAs
        for period in self.sma_periods:
            out[f"SMA_{period}"] = out["Close"].rolling(window=period, min_periods=period).mean()

        # Volume SMA (30 by default)
        out["Volume_SMA"] = out["Volume"].rolling(
            window=self.volume_lookback, min_periods=self.volume_lookback
        ).mean()

        # ATR (needed for atr_pct + risk label)
        high = out["High"]
        low = out["Low"]
        close = out["Close"]
        tr0 = (high - low).abs()
        tr1 = (high - close.shift()).abs()
        tr2 = (low - close.shift()).abs()
        tr = pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)
        out["ATR"] = tr.rolling(14, min_periods=14).mean()

        return out

    def _calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        low_min = df["Low"].rolling(window=period, min_periods=period).min()
        high_max = df["High"].rolling(window=period, min_periods=period).max()
        denom = (high_max - low_min).replace(0, np.nan)
        return 100.0 * (df["Close"] - low_min) / denom

    def _calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        tp = (df["High"] + df["Low"] + df["Close"]) / 3
        sma_tp = tp.rolling(window=period, min_periods=period).mean()
        mad = tp.rolling(window=period, min_periods=period).apply(
            lambda x: (x - x.mean()).abs().mean(), raw=False
        )
        mad_safe = mad.replace(0, np.nan)
        return (tp - sma_tp) / (0.015 * mad_safe)

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        df_copy = df.copy()
        df_copy["tr0"] = (df_copy["High"] - df_copy["Low"]).abs()
        df_copy["tr1"] = (df_copy["High"] - df_copy["Close"].shift()).abs()
        df_copy["tr2"] = (df_copy["Low"] - df_copy["Close"].shift()).abs()
        tr = df_copy[["tr0", "tr1", "tr2"]].max(axis=1)
        return tr.rolling(period, min_periods=period).mean()

    def _calculate_roc(self, df: pd.DataFrame, period: int = 12) -> pd.Series:
        prev = df["Close"].shift(period)
        prev_safe = prev.replace(0, np.nan)
        return ((df["Close"] - prev) / prev_safe) * 100.0

    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_max = df["High"].rolling(window=period, min_periods=period).max()
        low_min = df["Low"].rolling(window=period, min_periods=period).min()
        denom = (high_max - low_min).replace(0, np.nan)
        return -100.0 * (high_max - df["Close"]) / denom

    def calculate_rsi(self, df: pd.DataFrame, period: int | None = None) -> pd.Series:
        period = period or self.rsi_period
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=period - 1, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        flat = (avg_gain == 0) & (avg_loss == 0)
        return rsi.mask(flat, 50.0)

    def calculate_macd(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = df["Close"].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_bollinger(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
        sma = df["Close"].rolling(window=self.bb_period, min_periods=self.bb_period).mean()
        std = df["Close"].rolling(window=self.bb_period, min_periods=self.bb_period).std(ddof=0)
        upper = sma + (self.bb_std * std)
        lower = sma - (self.bb_std * std)
        return upper, sma, lower

    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> dict:
        latest = df.iloc[-1]
        return {
            "close": latest["Close"],
            "rsi": latest.get("RSI", np.nan),
            "macd": latest.get("MACD", np.nan),
            "macd_signal": latest.get("MACD_Signal", np.nan),
            "macd_hist": latest.get("MACD_Hist", np.nan),
            "bb_upper": latest.get("BB_Upper", np.nan),
            "bb_middle": latest.get("BB_Middle", np.nan),
            "bb_lower": latest.get("BB_Lower", np.nan),
            "sma_20": latest.get("SMA_20", np.nan),
            "sma_50": latest.get("SMA_50", np.nan),
            "sma_200": latest.get("SMA_200", np.nan),
            "volume": latest["Volume"],
            "volume_sma": latest.get("Volume_SMA", np.nan),
            "stochastic": latest.get("Stochastic", np.nan),
            "cci": latest.get("CCI", np.nan),
            "atr": latest.get("ATR", np.nan),
            "williams_r": latest.get("Williams_R", np.nan),
            "roc": latest.get("ROC", np.nan),
            "momentum": latest.get("Momentum", np.nan),
        }

