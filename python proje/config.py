"""
Uygulama Konfigürasyonu
"""

# PySide6 arayüzü ve marka adı
APP = {
    "name": "Nyron",
}

# Veri Parametreleri
DATA = {
    "period": "2y",              # 2 yıllık veri
    "interval": "1d",            # Günlük
    "min_data_points": 30,       # Minimum 30 gün veri gerekli
}

# Piyasa referansı (göreli güç — Yahoo Finance sembolü)
BENCHMARK = {
    "ticker": "XU100.IS",
    "enabled": True,
    "history_period": "6mo",
    # Üst çip başlığı: evren XU500 ile uyumlu görünen etiket (veri hâlâ ticker üzerinden)
    "ui_chip_caption": "XU500.IS",
}

# Profesyonel tarama eşikleri (UI filtreleriyle uyumlu)
SCREEN = {
    "min_vol_ratio_liquidity": 1.0,  # "Yüksek likidite" filtresi: son gün hacmi ≥ bu × 30g ort.
    "export_dir": "outputs",
    # Kombinasyon filtreleri (onay kutuları) — eşikler
    "filter_atr_high_pct": 2.5,
    "filter_atr_low_pct": 1.5,
    "filter_score_strong": 70,
    "filter_score_weak": 40,
}

# İndikatör Parametreleri
INDICATORS = {
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
    "sma_periods": [20, 50, 200],
    "volume_lookback": 30,
}

# Sinyal Skorlama
SCORING = {
    "rsi_weight": 0.25,
    "macd_weight": 0.30,
    "bollinger_weight": 0.20,
    "volume_weight": 0.15,
    "sma_weight": 0.10,
    "buy_threshold": 65,
    "sell_threshold": 35,
    # Arayüz: sinyal metni (Güçlü al / Al, Güçlü sat / Sat) eşikleri
    "ui_strong_buy_score": 73,
    "ui_strong_sell_score": 30,
    # Fırsatlar sekmesi: sadece BUY + skor eşiği + aşırı alımda (RSI) listeye alma
    "opportunity_min_score": 68,
    "opportunity_max_rsi": 73,
    "opportunity_require_buy_signal": True,
}

# Anomaly Detection
ANOMALY = {
    "bb_breakout": True,
    "volume_spike": 1.5,
    "rsi_extreme": True,
    "price_gap_percent": 2.0,
    "volume_drop": 0.5,
}

# Veritabanı
DATABASE = {
    "file": "cache.db",
    "cache_hours": 24,
}

# Logging
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/app.log",
}

# Tipografi (Windows: Segoe UI; yoksa Tk varsayılanı)
TYPOGRAPHY = {
    "family": "Segoe UI",
    "mono": "Consolas",
    "size_xs": 8,
    "size_sm": 9,
    "size_md": 10,
    "size_lg": 11,
    "size_xl": 13,
    "size_display": 14,
    "size_title": 15,
    "size_subtitle": 17,
    "size_hero": 21,
}

# Renk temaları (uygulama + detay penceresi)
THEMES = {
    "dark": {
        "bg": "#0a0e14",
        "panel": "#121922",
        "panel_alt": "#171f2a",
        "card": "#1c2633",
        "border": "#2d3d52",
        "text": "#e8eef4",
        "muted": "#8a9caf",
        "accent": "#3dd9a8",
        "blue": "#6b9fff",
        "green": "#45d688",
        "red": "#f0787c",
        "orange": "#e8a84a",
        "yellow": "#e4d14a",
        "gold": "#e8c96b",
        "log_bg": "#0c1118",
        "table_bg": "#0e141c",
        "select": "#243548",
        "buy_bg": "#14261c",
        "sell_bg": "#2a1a1e",
        "wait_bg": "#2a2418",
        "warn_bg": "#2c2618",
        "gainer_bg": "#152a1f",
        "loser_bg": "#2a1818",
    },
    "light": {
        "bg": "#eef2f7",
        "panel": "#ffffff",
        "panel_alt": "#e8eef6",
        "card": "#f4f7fb",
        "border": "#c5d0de",
        "text": "#1a2330",
        "muted": "#5c6b7d",
        "accent": "#0d9f73",
        "blue": "#3d6df0",
        "green": "#1e8f54",
        "red": "#c93d40",
        "orange": "#c9781a",
        "yellow": "#a67c00",
        "gold": "#b8860b",
        "log_bg": "#f8fafc",
        "table_bg": "#fbfcfe",
        "select": "#d4e4f7",
        "buy_bg": "#e4f5ec",
        "sell_bg": "#fce8ea",
        "wait_bg": "#f5efe4",
        "warn_bg": "#f7efd8",
        "gainer_bg": "#e6f5ed",
        "loser_bg": "#fceaea",
    },
}

# UI
UI = {
    "window_width": 1440,
    "window_height": 900,
    "theme": "dark",
    "font_main": ("Segoe UI", 10),
    "font_title": ("Segoe UI", 14, "bold"),
}

# BIST 500 (XU500) evreni — liste Borsa İstanbul CSV ile yenilenir, önbellek: data/bist500.txt
UNIVERSE = {
    "name": "BIST 500 (XU500)",
    "borsa_csv_url": "https://www.borsaistanbul.com/datum/hisse_endeks_ds.csv",
    "index_code": "XU500",
    "cache_max_age_hours": 168,  # 7 gün sonra otomatik yenileme denemesi
}

# Dosyalar (yollar proje köküne göre)
FILES = {
    "bist500_cache": "data/bist500.txt",
    "bist500_meta": "data/bist500.meta.txt",
    "output_report": "outputs/report.html",
}
