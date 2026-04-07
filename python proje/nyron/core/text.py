from __future__ import annotations

import pandas as pd

from config import SCORING


def format_signal_tr(signal: str | None, score: float | int | None) -> str:
    sig = str(signal or "WAIT").strip().upper()
    try:
        sc = float(score)
        if pd.isna(sc):
            sc = 50.0
    except (TypeError, ValueError):
        sc = 50.0
    bt = float(SCORING.get("buy_threshold", 65))
    st = float(SCORING.get("sell_threshold", 35))
    strong_buy = float(SCORING.get("ui_strong_buy_score", bt + 8))
    strong_sell = float(SCORING.get("ui_strong_sell_score", max(0.0, st - 5)))
    if sig == "BUY":
        return "Güçlü al" if sc >= strong_buy else "Al"
    if sig == "SELL":
        return "Güçlü sat" if sc <= strong_sell else "Sat"
    if sig == "WAIT":
        return "Tut"
    return sig

