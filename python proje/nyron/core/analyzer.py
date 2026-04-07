"""
Ana analiz motoru.
"""

from __future__ import annotations

import logging

import pandas as pd

from config import BENCHMARK
from nyron.core.anomalies import AnomalyDetector
from nyron.core.indicators import IndicatorCalculator
from nyron.core.metrics import build_thesis_line, compute_equity_metrics, fetch_benchmark_20d_return
from nyron.core.signal_model import SignalGenerator
from nyron.data.fetcher import DataFetcher
from nyron.data.universe import StockReader

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """Tüm analiz sürecini koordine eder."""

    def __init__(self):
        self.stock_reader = StockReader()
        self.data_fetcher = DataFetcher()
        self.indicator_calc = IndicatorCalculator()
        self.anomaly_detector = AnomalyDetector()
        self.signal_gen = SignalGenerator()

        self.all_data: dict = {}
        self.results_dict: dict = {}
        self.benchmark_20d_return: float | None = None

    def analyze(self, progress_callback=None) -> list:
        logger.info("=" * 60)
        logger.info("ANALİZ BAŞLATILDI")
        logger.info("=" * 60)

        logger.info("\n1️⃣  Hisse listesi okunuyor...")
        stocks = self.stock_reader.read_stocks()
        if not stocks:
            logger.error("❌ Hisse listesi boş!")
            return []

        logger.info("\n2️⃣  %s hisse senedinden veri çekiliyor...", len(stocks))
        stock_data = self.data_fetcher.fetch(stocks, progress_callback=progress_callback)
        if not stock_data:
            logger.error("❌ Veri çekme başarısız!")
            return []

        # `stock_data` büyük bir dict (çok sayıda DataFrame). Ek kopya bellek/CPU tüketiyor.
        # UI tarafı bu referansı sadece okumak için kullanıyor.
        self.all_data = stock_data

        logger.info("\n3️⃣  İndikatörler hesaplanıyor (%s hisse)...", len(stock_data))
        for symbol in list(stock_data.keys()):
            stock_data[symbol] = self.indicator_calc.calculate_core(stock_data[symbol])

        self.benchmark_20d_return = None
        bench_20 = None
        if BENCHMARK.get("enabled"):
            bench_20 = fetch_benchmark_20d_return(
                BENCHMARK["ticker"],
                period=BENCHMARK.get("history_period", "6mo"),
            )
            self.benchmark_20d_return = bench_20
            if bench_20 is not None:
                logger.info("Referans endeks %s ~20 işlem günü getiri: %.2f%%", BENCHMARK["ticker"], bench_20)
            else:
                logger.warning("Referans endeks getirisi alınamadı; göreli güç sütunu boş kalabilir.")

        logger.info("\n4️⃣  Sinyal ve Anomali tespit ediliyor...")
        results = []

        for symbol, df in stock_data.items():
            try:
                indicators = IndicatorCalculator.get_latest_indicators(df)
                signal_result = self.signal_gen.generate_signal(indicators)
                anomaly_result = self.anomaly_detector.detect(df)

                result = {
                    "symbol": symbol,
                    "price": round(float(indicators["close"]), 2),
                    "rsi": round(float(indicators["rsi"]), 1) if not pd.isna(indicators["rsi"]) else "N/A",
                    "macd": "↑" if indicators["macd_hist"] > 0 else "↓" if pd.notna(indicators["macd_hist"]) else "N/A",
                    "score": signal_result["score"],
                    "signal": signal_result["signal"],
                    "signal_color": signal_result["color"],
                    "anomaly": "⚠️ ANOMALI" if anomaly_result["has_anomaly"] else "✓ NORMAL",
                    "anomaly_color": anomaly_result["color"],
                    "anomaly_reason": ", ".join(anomaly_result["reasons"]),
                    "anomaly_severity": anomaly_result["severity"],
                }

                result.update(compute_equity_metrics(df, bench_20))
                result["thesis"] = build_thesis_line(result, result["signal"], result["score"])
                results.append(result)

                _d = signal_result.get("details") or {}
                self.results_dict[symbol] = {
                    "score": signal_result["score"],
                    "signal": signal_result["signal"],
                    "macd_score": _d.get("macd_score", 0),
                    "bb_score": _d.get("bollinger_score", 0),
                    "volume_score": _d.get("volume_score", 0),
                    "sma_score": _d.get("sma_score", 0),
                    "rsi_score": _d.get("rsi_score", 0),
                    "anomalies": anomaly_result,
                    "rsi": result["rsi"],
                    "macd": result["macd"],
                    "anomaly_color": result["anomaly_color"],
                    "pct_1d": result.get("pct_1d"),
                    "pct_5d": result.get("pct_5d"),
                    "pct_20d": result.get("pct_20d"),
                    "pct_60d": result.get("pct_60d"),
                    "atr_pct": result.get("atr_pct"),
                    "vol_ratio": result.get("vol_ratio"),
                    "trend_label": result.get("trend_label"),
                    "rs_20d": result.get("rs_20d"),
                    "risk_volatility": result.get("risk_volatility"),
                    "thesis": result.get("thesis"),
                    "benchmark_20d_note": bench_20,
                }

                # Tek tek 500 satır terminal logu yerine, bunu DEBUG'a çekiyoruz.
                logger.debug(
                    "  %s: Skor=%5.1f Signal=%4s Anomaly=%s",
                    symbol,
                    signal_result["score"],
                    signal_result["signal"],
                    "⚠️" if anomaly_result["has_anomaly"] else "✓",
                )

            except Exception as e:
                logger.error("  ❌ %s analiz hatası: %s", symbol, e)

        results.sort(key=lambda x: x["score"], reverse=True)
        logger.info("\n" + "=" * 60)
        logger.info("✅ %s hisse analiz edildi", len(results))
        logger.info("=" * 60)
        return results

