# -*- coding: utf-8 -*-
"""Hisse detay penceresi için saf veri/metin yardımcıları (Qt / Tk ortak mantık)."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def safe_ratio(numerator, denominator) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or not denominator:
        return 0.0
    return float(numerator) / float(denominator)


def recommended_chart_days(df: pd.DataFrame) -> int:
    total = len(df)
    if total >= 140:
        return 90
    if total >= 90:
        return 75
    if total >= 60:
        return 60
    return max(30, total)


def chart_level_summary(df: pd.DataFrame, chart_days: int, close_price: float) -> str:
    if df.empty or chart_days < 10:
        return "D — | R —"
    window = df.tail(chart_days)
    lows = window["Low"].values
    highs = window["High"].values
    closes = window["Close"].values

    support = []
    for idx in range(5, len(lows) - 5):
        if lows[idx] == min(lows[idx - 5 : idx + 5]):
            support.append(round(float(lows[idx]), 2))

    resistance = []
    for idx in range(5, len(highs) - 5):
        if highs[idx] == max(highs[idx - 5 : idx + 5]):
            resistance.append(round(float(highs[idx]), 2))

    support = list(dict.fromkeys(support))
    mean_c = float(closes.mean()) if len(closes) else 0
    if mean_c > 0:
        support = [v for i, v in enumerate(support) if i == 0 or abs(v - support[i - 1]) > mean_c * 0.02][:3]

    resistance = list(dict.fromkeys(resistance))
    resistance.sort(reverse=True)
    if mean_c > 0:
        resistance = [v for i, v in enumerate(resistance) if i == 0 or abs(v - resistance[i - 1]) > mean_c * 0.02][:3]

    nearest_support = max((v for v in support if v <= close_price), default=(support[-1] if support else None))
    nearest_resistance = min((v for v in resistance if v >= close_price), default=(resistance[0] if resistance else None))

    st = f"D {nearest_support:.2f}" if nearest_support is not None else "D —"
    rt = f"R {nearest_resistance:.2f}" if nearest_resistance is not None else "R —"
    return f"{st} | {rt}"


def _rsi_card_color(rsi: float) -> str:
    if rsi > 70 or rsi < 30:
        return "red"
    if 40 < rsi < 60:
        return "green"
    return "yellow"


def collect_indicator_cards(df: pd.DataFrame, results: dict) -> list[dict[str, Any]]:
    """İndikatör sekmesi kartları."""
    last = df.iloc[-1]
    close = float(last.get("Close", 0) or 0)
    cards: list[dict[str, Any]] = []

    rsi = last.get("RSI")
    if pd.notna(rsi):
        rsi = float(rsi)
        cards.append({
            "title": "RSI (14)",
            "value": f"{rsi:.2f}",
            "color": _rsi_card_color(rsi),
            "status": (
                "Aşırı alım" if rsi >= 70 else "Yukarı momentum" if rsi >= 60 else "Dengeli alan" if rsi >= 40 else "Aşağı momentum" if rsi >= 30 else "Aşırı satım"
            ),
            "note": "Momentum dengesi",
        })

    macd = last.get("MACD")
    signal = last.get("MACD_Signal")
    if pd.notna(macd) and pd.notna(signal):
        macd, signal = float(macd), float(signal)
        cards.append({
            "title": "MACD",
            "value": f"{macd:.5f}",
            "color": "green" if macd > signal else "red",
            "status": "Yukarı kesişim" if macd > signal else "Aşağı kesişim",
            "note": f"Sinyal farkı {(macd - signal):+.4f}",
        })

    stoch = last.get("Stochastic")
    if pd.notna(stoch):
        stoch = float(stoch)
        cards.append({
            "title": "Stochastic",
            "value": f"{stoch:.2f}%",
            "color": "red" if stoch > 80 else "green" if stoch < 20 else "yellow",
            "status": "Aşırı alım" if stoch > 80 else "Aşırı satım" if stoch < 20 else "Nötr alan",
            "note": "Kısa vade ivme",
        })

    williams = last.get("Williams_R")
    if pd.notna(williams):
        w = float(williams)
        cards.append({
            "title": "Williams %R",
            "value": f"{w:.2f}",
            "color": "red" if w > -20 else "green" if w < -80 else "yellow",
            "status": "Aşırı alım" if w > -20 else "Aşırı satım" if w < -80 else "Denge",
            "note": "Bant içi konum",
        })

    bb_upper = last.get("BB_Upper")
    bb_lower = last.get("BB_Lower")
    if pd.notna(bb_upper) and pd.notna(bb_lower):
        bu, bl = float(bb_upper), float(bb_lower)
        band_span = bu - bl
        band_pos = ((close - bl) / band_span * 100) if band_span else 50.0

        def bb_status() -> str:
            if close > bu:
                return "Üst bandı aştı"
            if close < bl:
                return "Alt banda indi"
            return "Band içinde"

        cards.append({
            "title": "Bollinger Bands",
            "value": f"{band_pos:.1f}%",
            "color": "red" if close > bu or close < bl else "green",
            "status": bb_status(),
            "note": f"Band aralığı {band_span:.2f} ₺",
        })

    cci = last.get("CCI")
    if pd.notna(cci):
        c = float(cci)
        cards.append({
            "title": "CCI",
            "value": f"{c:.2f}",
            "color": "green" if abs(c) < 100 else "yellow" if abs(c) < 200 else "red",
            "status": "Normal" if abs(c) < 100 else "Güçlü" if abs(c) < 200 else "Aşırı",
            "note": "Ortalamadan sapma",
        })

    atr = last.get("ATR")
    atr_mean = df["ATR"].dropna().mean() if "ATR" in df.columns else None
    if pd.notna(atr):
        atr = float(atr)
        high_vol = pd.notna(atr_mean) and float(atr_mean) > 0 and atr > float(atr_mean) * 1.5
        cards.append({
            "title": "ATR",
            "value": f"{atr:.4f}",
            "color": "red" if high_vol else "green",
            "status": "Volatilite yüksek" if high_vol else "Volatilite normal",
            "note": f"Ortalamaya göre {safe_ratio(atr, atr_mean):.2f}×",
        })

    roc = last.get("ROC")
    if pd.notna(roc):
        roc = float(roc)
        cards.append({
            "title": "ROC",
            "value": f"{roc:+.2f}%",
            "color": "green" if roc >= 0 else "red",
            "status": "Pozitif hız" if roc >= 0 else "Negatif hız",
            "note": "12 günlük değişim",
        })

    for period in (20, 50, 200):
        sma = last.get(f"SMA_{period}")
        if pd.notna(sma):
            sma = float(sma)
            gap = ((close - sma) / sma * 100) if sma else 0.0
            cards.append({
                "title": f"SMA {period}",
                "value": f"{sma:.2f} ₺",
                "color": "green" if close >= sma else "red",
                "status": "Fiyat üstünde" if close >= sma else "Fiyat altında",
                "note": f"Fark {gap:+.2f}%",
            })

    if len(df) >= 30:
        vol = float(df["Close"].pct_change().tail(30).std() * 100)
        cards.append({
            "title": "30G Volatilite",
            "value": f"{vol:.2f}%",
            "color": "red" if vol > 3 else "yellow" if vol > 1.5 else "green",
            "status": "Yüksek" if vol > 3 else "Orta" if vol > 1.5 else "Düşük",
            "note": "Kapanış oynaklığı",
        })

    return cards


def signal_label_tr(results: dict) -> str:
    from nyron.core.text import format_signal_tr

    return format_signal_tr(results.get("signal"), results.get("score"))


def indicator_narrative(df: pd.DataFrame, results: dict) -> str:
    last = df.iloc[-1]
    rsi = last.get("RSI")
    macd = last.get("MACD")
    sig = last.get("MACD_Signal")
    roc = last.get("ROC")
    parts = [f"Sinyal görünümü {signal_label_tr(results).lower()}."]
    if pd.notna(rsi):
        parts.append(f"RSI {float(rsi):.1f} seviyesinde.")
    if pd.notna(macd) and pd.notna(sig):
        parts.append("MACD pozitif tarafta." if float(macd) > float(sig) else "MACD baskısı devam ediyor.")
    if pd.notna(roc):
        r = float(roc)
        parts.append(f"ROC {r:+.2f}% ile hız {'pozitif' if r >= 0 else 'negatif'}.")
    return " ".join(parts)


def summary_components(df: pd.DataFrame, results: dict) -> list[tuple[str, float, str]]:
    """(başlık, 0-100 değer, renk anahtarı)."""
    # Prefer model component scores if available (avoids "default 50" when raw indicators are missing).
    try:
        mr = float(results.get("rsi_score")) if results.get("rsi_score") is not None else None
        mm = float(results.get("macd_score")) if results.get("macd_score") is not None else None
        mb = float(results.get("bb_score")) if results.get("bb_score") is not None else None
        mv = float(results.get("volume_score")) if results.get("volume_score") is not None else None
        ms = float(results.get("sma_score")) if results.get("sma_score") is not None else None
        model_ok = all(x is not None for x in (mr, mm, mb, mv, ms))
    except Exception:
        model_ok = False

    def sc_col(v: float) -> str:
        if v >= 70:
            return "green"
        if v >= 50:
            return "orange"
        return "red"

    if model_ok:
        risk_score = 75.0 if not (results.get("anomalies") or {}).get("has_anomaly") else 35.0
        # Trend alignment: combine MACD + SMA components for a single "trend" bar.
        trend_score = (float(mm) * 0.6) + (float(ms) * 0.4)
        return [
            ("Momentum dengesi", float(mr), sc_col(float(mr))),
            ("Trend uyumu", float(trend_score), sc_col(float(trend_score))),
            ("Bant konumu", float(mb), sc_col(float(mb))),
            ("Hacim teyidi", float(mv), sc_col(float(mv))),
            ("Risk temizliği", float(risk_score), sc_col(float(risk_score))),
        ]

    last = df.iloc[-1]
    close = last.get("Close")
    rsi = last.get("RSI")
    macd = last.get("MACD")
    macd_signal = last.get("MACD_Signal")
    bb_upper = last.get("BB_Upper")
    bb_lower = last.get("BB_Lower")
    volume = last.get("Volume")
    volume_sma = df["Volume"].tail(30).mean()
    sma20 = last.get("SMA_20")
    sma50 = last.get("SMA_50")

    rsi_score = 50.0
    if pd.notna(rsi):
        r = float(rsi)
        if r < 30:
            rsi_score = 85
        elif r <= 45:
            rsi_score = 65
        elif r <= 60:
            rsi_score = 55
        elif r <= 70:
            rsi_score = 40
        else:
            rsi_score = 20

    trend_score = 50.0
    if pd.notna(macd) and pd.notna(macd_signal) and pd.notna(sma20) and pd.notna(sma50):
        m, ms, s20, s50 = float(macd), float(macd_signal), float(sma20), float(sma50)
        if m > ms and s20 > s50:
            trend_score = 84
        elif m > ms:
            trend_score = 68
        elif s20 > s50:
            trend_score = 58
        else:
            trend_score = 28

    band_score = 50.0
    if pd.notna(close) and pd.notna(bb_upper) and pd.notna(bb_lower) and float(bb_upper) != float(bb_lower):
        position = (float(close) - float(bb_lower)) / (float(bb_upper) - float(bb_lower))
        band_score = max(0.0, min(100.0, 100.0 - position * 100.0))

    vr = safe_ratio(volume, volume_sma)
    volume_score = 35.0
    if vr >= 1.5:
        volume_score = 90
    elif vr >= 1.0:
        volume_score = 70
    elif vr >= 0.7:
        volume_score = 50

    risk_score = 75.0 if not (results.get("anomalies") or {}).get("has_anomaly") else 35.0

    return [
        ("Momentum dengesi", rsi_score, sc_col(rsi_score)),
        ("Trend uyumu", trend_score, sc_col(trend_score)),
        ("Bant konumu", band_score, sc_col(band_score)),
        ("Hacim teyidi", volume_score, sc_col(volume_score)),
        ("Risk temizliği", risk_score, sc_col(risk_score)),
    ]


def summary_notes_list(df: pd.DataFrame, results: dict) -> list[str]:
    last = df.iloc[-1]
    close = float(last.get("Close", 0) or 0)
    sma20 = last.get("SMA_20")
    sma50 = last.get("SMA_50")
    vr = safe_ratio(last.get("Volume"), df["Volume"].tail(30).mean())
    notes = [
        f"Ana teknik skor {results.get('score', 0):.1f}/100 seviyesinde.",
        f"Hacim 30 günlük ortalamanın {vr:.2f} katı.",
    ]
    if pd.notna(sma20):
        s20 = float(sma20)
        notes.append(f"Fiyat SMA20 seviyesine göre {((close - s20) / s20 * 100):+.2f}% konumda.")
    if pd.notna(sma50):
        s50 = float(sma50)
        notes.append(f"Orta vadeli görünüm için SMA50 farkı {((close - s50) / s50 * 100):+.2f}%.")
    if (results.get("anomalies") or {}).get("has_anomaly"):
        notes.append("Anomali tespiti bulunduğu için sinyal gücü tek başına yeterli kabul edilmemeli.")
    else:
        notes.append("Anomali görülmediği için teknik görünüm daha temiz okunabiliyor.")
    return notes


def discipline_notes_list(results: dict) -> list[str]:
    signal = results.get("signal", "WAIT")
    base = [
        "Kararı yalnızca tek gün verisine göre değil, birkaç gün teyitle okumak daha sağlıklı.",
        "Hacim eşlik etmeyen hareketlerde giriş iştahı düşürülmeli.",
        "Teknik skor yüksek olsa bile zarar kes ve pozisyon boyutu kuralları korunmalı.",
    ]
    if signal == "BUY":
        base.append("Alış senaryosunda ilk takip seviyesi kısa vadeli destek ve SMA20 çevresi olmalı.")
    elif signal == "SELL":
        base.append("Satış baskısı senaryosunda tepki hareketi gelse bile trend teyidi beklenmeli.")
    else:
        base.append("Bekle senaryosunda net yön oluşmadan agresif işlem aramak gereksiz risk üretir.")
    return base


def decision_sentence(df: pd.DataFrame, results: dict, ticker_clean: str) -> str:
    signal = signal_label_tr(results)
    anomaly_txt = "UYARI VAR" if (results.get("anomalies") or {}).get("has_anomaly") else "TEMİZ"
    last = df.iloc[-1]
    rsi = last.get("RSI")
    vr = safe_ratio(last.get("Volume"), df["Volume"].tail(30).mean())
    rsi_text = f"RSI {float(rsi):.1f}" if pd.notna(rsi) else "RSI verisi sınırlı"
    return (
        f"{ticker_clean} için teknik çerçeve şu an {signal.lower()} eğiliminde. "
        f"{rsi_text}, hacim oranı {vr:.2f}× ve anomali durumu {anomaly_txt}. "
        "Bu tablo kısa vadeli fırsat sunsa da tek başına işlem emri yerine teyit mekanizması olarak okunmalı."
    )


def anomaly_direction_label(results: dict) -> str:
    s = results.get("signal", "WAIT")
    if s == "BUY":
        return "Alım yönlü"
    if s == "SELL":
        return "Satım yönlü"
    return "Nötr / bekle"


def severity_caption(severity: str) -> str:
    s = (severity or "none").lower()
    if s == "high":
        return "Kısa vadede güçlü sapma işareti"
    if s == "medium":
        return "İzlenmesi gereken belirgin sapma"
    if s == "low":
        return "Düşük yoğunluklu alarm"
    return "Ek teknik sapma algılanmadı"


def anomaly_overview_text(results: dict, ticker_clean: str, direction: str) -> str:
    anomaly = results.get("anomalies") or {}
    reasons = anomaly.get("reasons") or []
    severity = anomaly.get("severity", "none")
    cap = severity_caption(severity).lower()

    if not anomaly.get("has_anomaly"):
        return (
            f"{ticker_clean} için şu an aktif teknik uyumsuzluk tespit edilmedi. "
            "Fiyat, hacim ve momentum bileşenlerinin birbirini bozan ek bir alarm üretmediğini gösterir. "
            f"Mevcut tablo {direction.lower()} okunsa bile karar kalitesini korumak için "
            "destek-direnç, hacim teyidi ve pozisyon boyutu disiplini birlikte izlenmelidir."
        )

    return (
        f"{ticker_clean} hissesinde toplam {len(reasons)} adet teknik uyumsuzluk bulundu. "
        f"Alarm şiddeti {str(severity).upper()} seviyesinde ve bu tablo {direction.lower()} bir ana sinyal ile birlikte okunuyor. "
        f"Bu seviye {cap} anlamına gelir; sinyal tamamen geçersiz sayılmasa da tek başına güvenle kullanılmamalıdır."
    )


def anomaly_blocks(details: dict) -> list[dict[str, str]]:
    mapping = [
        ("bb_breakout", "Bollinger band kırılımı", "Fiyat beklenen volatilite koridorunun dışına taşmış olabilir.", "Bant dışı hareketlerde dönüş teyidi gelmeden agresif giriş yapılmamalı."),
        ("volume_spike", "Hacim sıçraması", "Ani ilgi artışı haber veya güçlü emir akışı olabileceğini düşündürür.", "Hacim artışı yön teyidiyle birleşmiyorsa sahte hareket riski düşünülmeli."),
        ("rsi_extreme", "RSI aşırı bölge", "Aşırı alım/satım bölgesi sert tepki ihtimalini artırır.", "Aşırı bölgelerde giriş zamanlaması küçük parçalı yönetilmeli."),
        ("price_gap", "Fiyat boşluğu", "Açılış-kapanış kopması kısa vadeli dengesizlik gösterebilir.", "Gap sonrası ilk tepki değil, gap’in korunup korunmadığı izlenmeli."),
        ("volume_drop", "Hacim düşüşü", "Hareketin arkasındaki katılım zayıflamış olabilir.", "Hacim düşüşünde trend devam görünse bile teyit gücü azalır."),
    ]
    out = []
    for key, title, desc, mgmt in mapping:
        if key in (details or {}):
            out.append({"title": title, "detail": str(details[key]), "description": desc, "management": mgmt})
    return out


def anomaly_management_notes(anomaly: dict) -> list[str]:
    severity = (anomaly.get("severity") or "none").lower()
    notes = [
        "Uyumsuzluk sinyalin yanlış olduğunu değil, güven seviyesinin düştüğünü anlatır.",
        "Alarm varken ana hedef kazancı zorlamak değil, hata maliyetini küçültmektir.",
        "Sinyal ile alarm aynı yöne bakmıyorsa işlem süresi kısaltılmalı ve teyit standardı yükseltilmelidir.",
    ]
    if severity == "high":
        notes.append("Yüksek şiddette yeni pozisyon açılacaksa parça parça giriş ve sıkı zarar kes düşünülmeli.")
    elif severity == "medium":
        notes.append("Orta şiddette alarmda işlem açılıyorsa hacim ve kapanış teyidi beklemek daha sağlıklıdır.")
    elif severity == "low":
        notes.append("Düşük şiddette alarm daha çok izleme uyarısıdır; standart kurallar gevşetilmemelidir.")
    return notes


def anomaly_discipline_notes(anomaly: dict) -> list[str]:
    severity = (anomaly.get("severity") or "none").lower()
    notes = []
    if severity == "high":
        notes.append("Yüksek şiddetli alarmda ilk amaç fırsat kovalamak değil, sermayeyi korumaktır.")
    elif severity == "medium":
        notes.append("Orta şiddetli alarmda teyit almadan yapılan işlemler performansı bozabilir.")
    elif severity == "low":
        notes.append("Düşük şiddetli alarm sinyali iptal etmez ama karar kalitesini düşürür.")
    else:
        notes.append("Ek uyumsuzluk bulunmadığı için teknik tablo daha temiz okunuyor.")

    if anomaly.get("has_anomaly"):
        notes.extend([
            "Alarm varken hacim, trend ve destek-direnç birlikte okunmalı; tek metrikle karar verilmemeli.",
            "Pozisyon büyüklüğü normal senaryoya göre azaltılmalı ve zarar kes mesafesi baştan tanımlanmalı.",
        ])
    else:
        notes.append("Temiz durum sinyalin daha sağlıklı olduğu anlamına gelir; yine de risk yönetimi zorunludur.")
    return notes


def anomaly_action_items(anomaly: dict) -> list[str]:
    severity = (anomaly.get("severity") or "none").lower()
    if not anomaly.get("has_anomaly"):
        return [
            "Grafikte trend, destek ve hacim teyidini birlikte okumaya devam et.",
            "Alarm temiz olsa da tek sinyalle pozisyon büyütme.",
            "Bir sonraki taramada değişim olup olmadığını karşılaştır.",
        ]
    items = [
        "Alarm sebebini grafik ve hacim paneli ile eşleştir.",
        "Hisseye giriş düşünülüyorsa pozisyon boyutunu düşür.",
        "Destek-direnç kırılımı teyit edilmeden acele karar verme.",
    ]
    if severity == "high":
        items[0] = "Yüksek risk olduğu için fiyat davranışını birkaç bar daha izle."
    elif severity == "medium":
        items[1] = "Orta riskte teyit almadan agresif işlem boyutuna çıkma."
    return items


def fetch_yahoo_news(ticker_yahoo: str, ticker_clean: str) -> list[dict[str, str]]:
    """Yahoo Finance haber listesi (arka planda çağrılmak üzere)."""
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker_yahoo)
        raw = getattr(stock, "news", None) or []
        news_list: list[dict[str, str]] = []
        for item in raw[:12]:
            title = (item.get("title") or "").strip() or "Başlıksız"
            publisher = (item.get("publisher") or item.get("source") or "Yahoo Finance")
            link = (item.get("link") or "").strip()
            if not link:
                link = f"https://finance.yahoo.com/quote/{ticker_clean}"
            summary = (item.get("summary") or "").strip()
            news_list.append({"title": title, "source": publisher, "summary": summary, "link": link})

        if not news_list:
            news_list.append({
                "title": "Şu an haber listesi boş",
                "source": "Bilgi",
                "summary": (
                    "Yahoo Finance bu sembol için haber döndürmedi veya API geçici olarak veri vermiyor. "
                    "Güncel başlıklar için bağlantıyla sayfayı tarayıcıda açabilirsiniz."
                ),
                "link": f"https://finance.yahoo.com/quote/{ticker_clean}.IS",
            })
        return news_list
    except Exception as exc:
        logger.warning("Haber çekilemedi (%s): %s", ticker_yahoo, exc)
        return [{
            "title": "Haber yüklenemedi",
            "source": "Hata",
            "summary": str(exc)[:200],
            "link": f"https://finance.yahoo.com/quote/{ticker_clean}.IS",
        }]
