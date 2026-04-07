# -*- coding: utf-8 -*-
"""Hisse detayı: grafik, indikatör merkezi, uyumsuzluk, özet — tam sekme yapısı."""

from __future__ import annotations

import html
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nyron.core import controller as ac
from config import APP
from chart_generator import ChartGenerator
from nyron.core.favorites import FavoritesStore
from nyron.core.indicators import IndicatorCalculator
from nyron.core.metrics import build_opportunity_rationale
from qt_app import detail_helpers as dh
from qt_app import ui_icons as nui
from qt_app.styles import stylesheet_dark, stylesheet_light

logger = logging.getLogger(__name__)
_APP_NAME = APP.get("name", "Nyron")

_COL_TR = {
    "Open": "Açılış",
    "High": "En yüksek",
    "Low": "En düşük",
    "Close": "Kapanış",
    "Volume": "Hacim",
    "RSI": "RSI",
    "MACD": "MACD",
    "MACD_Signal": "MACD sinyal",
    "MACD_Hist": "MACD histogram",
    "BB_Upper": "BB üst",
    "BB_Middle": "BB orta",
    "BB_Lower": "BB alt",
    "SMA_20": "SMA 20",
    "SMA_50": "SMA 50",
    "SMA_200": "SMA 200",
    "ATR": "ATR",
    "Stochastic": "Stokastik",
    "CCI": "CCI",
    "Williams_R": "Williams %R",
    "ROC": "ROC",
    "Momentum": "Momentum (10g)",
}

_NUM_COLS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "RSI",
    "MACD",
    "MACD_Signal",
    "MACD_Hist",
    "BB_Upper",
    "BB_Middle",
    "BB_Lower",
    "SMA_20",
    "SMA_50",
    "SMA_200",
    "ATR",
    "Stochastic",
    "CCI",
    "Williams_R",
    "ROC",
    "Momentum",
]


class _NewsFetchThread(QThread):
    """Yahoo Finance haberleri — UI bloklanmaz."""

    done = Signal(list)
    failed = Signal(str)

    def __init__(self, ticker_full: str, ticker_clean: str):
        super().__init__()
        self._full = ticker_full
        self._clean = ticker_clean

    def run(self):
        try:
            self.done.emit(dh.fetch_yahoo_news(self._full, self._clean))
        except Exception as exc:
            logger.exception("Haber iş parçacığı")
            self.failed.emit(str(exc))


class DetailView(QWidget):
    """Hisse detayı — ana pencere içine gömülür veya bağımsız kullanım için QWidget."""

    back_requested = Signal()
    theme_toggle_requested = Signal()
    favorite_changed = Signal(str, bool)  # (ticker_clean, is_favorite)

    def __init__(self, parent, ticker_full: str, df, results_dict: dict, dark: bool = True):
        super().__init__(parent)
        self._dark = dark
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._apply_panel_stylesheet()

        self._df = df
        self._ticker_full = ticker_full
        self._ticker_clean = ticker_full.replace(".IS", "").strip()
        self._results: dict[str, Any] = dict(results_dict.get(ticker_full, {}) or {})
        self._fav_store = FavoritesStore()
        self._is_favorite = self._fav_store.is_favorite(self._ticker_clean)
        self._news_thread: _NewsFetchThread | None = None
        self._news_layout: QVBoxLayout | None = None

        # Detail view expects extended indicators for charts/cards/raw table.
        # Scan-time pipeline may only compute a "core" subset; complete it here per symbol.
        try:
            need = ("Stochastic", "CCI", "ROC", "Williams_R", "Momentum")
            if self._df is not None and not self._df.empty and any(c not in self._df.columns for c in need):
                self._df = IndicatorCalculator().calculate_all(self._df)
        except Exception:
            logger.exception("Detay indikatör tamamlama")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_chart_tab(), "Grafik")
        self._tabs.addTab(self._build_indicators_tab(), "İndikatörler")
        self._tabs.addTab(self._build_anomaly_tab(), "Uyumsuzluk")
        self._tabs.addTab(self._build_summary_tab(), "Özet")
        self._tabs.addTab(self._build_news_tab(), "Haberler")
        self._tabs.addTab(self._build_raw_tab(), "Ham veri")

        self._btn_nav_back = QPushButton()
        self._btn_nav_back.setObjectName("iconToolButton")
        self._btn_nav_back.setToolTip("Sonuçlar ekranına dön")
        self._btn_nav_back.clicked.connect(self.back_requested.emit)
        self._btn_nav_fav = QPushButton()
        self._btn_nav_fav.setObjectName("iconToolButton")
        self._btn_nav_fav.clicked.connect(self._toggle_favorite)
        self._btn_nav_theme = QPushButton()
        self._btn_nav_theme.setObjectName("iconToolButton")
        self._btn_nav_theme.clicked.connect(self.theme_toggle_requested.emit)

        nav_right = QWidget()
        nrl = QHBoxLayout(nav_right)
        nrl.setContentsMargins(0, 0, 2, 0)
        nrl.setSpacing(2)
        nrl.addWidget(self._btn_nav_back)
        nrl.addWidget(self._btn_nav_fav)
        nrl.addWidget(self._btn_nav_theme)

        self._tabs.setCornerWidget(nav_right, Qt.Corner.TopRightCorner)
        self._refresh_nav_action_icons()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._tabs, 1)

        self._start_news_fetch()

    def _apply_panel_stylesheet(self) -> None:
        self.setStyleSheet(stylesheet_dark() if self._dark else stylesheet_light())

    def apply_theme(self, dark: bool) -> None:
        self._dark = dark
        self._apply_panel_stylesheet()
        self._refresh_nav_action_icons()
        self._refresh_chart_theme()

    def _refresh_chart_theme(self) -> None:
        """Grafik canvas'ı tema değişiminde yeniden üret (Matplotlib style runtime'da tam değişmiyor)."""
        host = getattr(self, "_chart_host", None)
        outer = getattr(self, "_chart_outer", None)
        if host is None or outer is None:
            return
        try:
            old = getattr(self, "_chart_canvas", None)
            if old is not None:
                outer.removeWidget(old)
                old.setParent(None)
                old.deleteLater()
                self._chart_canvas = None
        except Exception:
            pass
        try:
            gen = ChartGenerator(dark=self._dark)
            canvas = gen.create_candlestick_chart_qt(self._df, self._ticker_clean)
            self._chart_canvas = canvas
            outer.addWidget(canvas, 1)
        except Exception:
            logger.exception("Tema: grafik yenileme")

    def _refresh_nav_action_icons(self) -> None:
        d = self._dark
        self._btn_nav_back.setIcon(nui.icon_back(d))
        self._btn_nav_back.setText("")
        if getattr(self, "_btn_nav_fav", None) is not None:
            self._btn_nav_fav.setText("★" if self._is_favorite else "☆")
            self._btn_nav_fav.setToolTip(
                "Favorilerden çıkar" if self._is_favorite else "Favorilere ekle"
            )
        if d:
            ic, tip = nui.icon_theme_to_light(), "Aydınlık temaya geç"
        else:
            ic, tip = nui.icon_theme_to_dark(), "Karanlık temaya geç"
        self._btn_nav_theme.setIcon(ic)
        self._btn_nav_theme.setText("")
        self._btn_nav_theme.setToolTip(tip)

    def _toggle_favorite(self) -> None:
        try:
            enabled = self._fav_store.toggle(self._ticker_clean)
            self._is_favorite = bool(enabled)
            self._refresh_nav_action_icons()
            self.favorite_changed.emit(self._ticker_clean, self._is_favorite)
        except Exception as exc:
            QMessageBox.warning(self, _APP_NAME, f"Favori güncellenemedi:\n{exc}")

    def shutdown_async(self) -> None:
        t = self._news_thread
        if t is None:
            return
        # QThread yaşam döngüsü: pencere kapanırken iş parçacığı objesi Qt tarafından
        # silinmiş olabiliyor (PySide wrapper dururken C++ objesi gidebiliyor).
        try:
            if t.isRunning():
                try:
                    t.requestInterruption()
                except RuntimeError:
                    pass
                try:
                    t.quit()
                except RuntimeError:
                    pass
                try:
                    t.wait(4000)
                except RuntimeError:
                    pass
        except RuntimeError:
            pass
        self._news_thread = None

    def closeEvent(self, event):
        self.shutdown_async()
        super().closeEvent(event)

    def _accent(self, key: str) -> str:
        if self._dark:
            return {
                "green": "#57d38c",
                "red": "#ff7b7b",
                "yellow": "#e6c86e",
                "orange": "#ff9f68",
                "blue": "#6b9fff",
            }.get(key, "#6b9fff")
        return {
            "green": "#0d9f73",
            "red": "#c62828",
            "yellow": "#b8860b",
            "orange": "#e65100",
            "blue": "#1d4ed8",
        }.get(key, "#3d6df0")

    def _section_header(self, title: str, subtitle: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 4, 0, 8)
        t = QLabel(title)
        t.setObjectName("sectionTitle")
        s = QLabel(subtitle)
        s.setObjectName("sectionSub")
        s.setWordWrap(True)
        v.addWidget(t)
        v.addWidget(s)
        return w

    def _header_tile(self, title: str, value: str, subtitle: str, value_color: str | None = None) -> QFrame:
        f = QFrame()
        f.setObjectName("detailTile")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(14, 12, 14, 12)
        lt = QLabel(title)
        lt.setObjectName("detailTileTitle")
        lv = QLabel(value)
        lv.setObjectName("detailTileValue")
        if value_color:
            lv.setStyleSheet(f"color: {value_color};")
        ls = QLabel(subtitle)
        ls.setObjectName("detailTileSub")
        ls.setWordWrap(True)
        lay.addWidget(lt)
        lay.addWidget(lv)
        lay.addWidget(ls)
        return f

    def _summary_tile(self, title: str, value: str, subtitle: str, value_color: str | None = None) -> QFrame:
        """Özet sekmesi kutuları — başlık, değer ve alt metin yatay/dikey ortada."""
        f = QFrame()
        f.setObjectName("detailTile")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.addStretch(1)
        lt = QLabel(title)
        lt.setObjectName("detailTileTitle")
        lt.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        lv = QLabel(value)
        lv.setObjectName("detailTileValue")
        lv.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        if value_color:
            lv.setStyleSheet(f"color: {value_color};")
        ls = QLabel(subtitle)
        ls.setObjectName("detailTileSub")
        ls.setWordWrap(True)
        ls.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(lt, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(lv, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(ls, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)
        return f

    def _build_chart_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        # Keep refs so we can rebuild the canvas on theme switch.
        self._chart_host = w
        self._chart_outer = outer
        self._chart_canvas = None
        df = self._df
        last = df.iloc[-1]
        close = float(last.get("Close", 0) or 0)
        open_p = float(last.get("Open", 0) or 0)
        daily_change = ((close - open_p) / open_p * 100.0) if open_p else 0.0
        chart_days = dh.recommended_chart_days(df)
        level_summary = dh.chart_level_summary(df, chart_days, close)
        ch_col = self._accent("green") if daily_change >= 0 else self._accent("red")

        hero = QHBoxLayout()
        hero.addWidget(
            self._header_tile(
                "Grafik görünümü",
                "Teknik harita",
                "Mum, hacim, RSI ve MACD tek panelde",
                self._accent("green"),
            ),
            1,
        )
        hero.addWidget(
            self._header_tile(
                "Günlük hareket",
                f"{daily_change:+.2f}%",
                f"Son fiyat {close:.2f} ₺",
                ch_col,
            ),
            1,
        )
        hero.addWidget(
            self._header_tile(
                "Destek / direnç",
                level_summary,
                f"Otomatik pencere: {chart_days} gün",
                self._accent("yellow"),
            ),
            1,
        )
        outer.addLayout(hero)

        try:
            gen = ChartGenerator(dark=self._dark)
            canvas = gen.create_candlestick_chart_qt(df, self._ticker_clean)
            self._chart_canvas = canvas
            outer.addWidget(canvas, 1)
        except Exception as exc:
            logger.exception("Grafik oluşturulamadı")
            outer.addWidget(QLabel(f"Grafik hatası: {exc}"))

        return w

    def _metric_card(self, info: dict[str, str]) -> QFrame:
        card = QFrame()
        card.setObjectName("detailPanel")
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        stripe = QFrame()
        stripe.setFixedHeight(4)
        stripe.setStyleSheet(f"background-color: {self._accent(info['color'])}; border: none; border-radius: 2px;")
        v.addWidget(stripe)
        inner = QVBoxLayout()
        inner.setContentsMargins(12, 10, 12, 12)
        t = QLabel(info["title"])
        t.setObjectName("detailTileTitle")
        val = QLabel(info["value"])
        val.setObjectName("detailTileValue")
        val.setStyleSheet(f"color: {self._accent(info['color'])};")
        st = QLabel(info["status"])
        st.setStyleSheet("font-weight: 600;")
        nt = QLabel(info["note"])
        nt.setObjectName("detailTileSub")
        nt.setWordWrap(True)
        inner.addWidget(t)
        inner.addWidget(val)
        inner.addWidget(st)
        inner.addWidget(nt)
        v.addLayout(inner)
        return card

    def _wrap_scroll(self, inner: QWidget) -> QScrollArea:
        # Give scroll areas stable names so light theme can force solid backgrounds
        # (prevents dark bleed-through in some Qt styles/palettes).
        inner.setObjectName("detailScrollInner")
        scroll = QScrollArea()
        scroll.setObjectName("detailScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(inner)
        return scroll

    def _build_indicators_tab(self) -> QWidget:
        container = QWidget()
        main_l = QVBoxLayout(container)

        left_inner = QWidget()
        left_l = QVBoxLayout(left_inner)
        left_l.addWidget(
            self._section_header(
                "İndikatör merkezi",
                "Temel metrikler ve teknik kartlar; ham sayılar «Ham veri», haberler «Haberler» sekmesindedir.",
            )
        )
        ind_guide = QFrame()
        ind_guide.setObjectName("detailPanel")
        igl = QVBoxLayout(ind_guide)
        igl.setContentsMargins(14, 12, 14, 12)
        ig_head = QLabel("Bu sekmede neler var?")
        ig_head.setObjectName("sectionTitle")
        igl.addWidget(ig_head)
        ig_txt = QLabel(
            "Üstteki kutular son işlem gününün fiyatı, model sinyali ve hacim oranını özetler. "
            "Renkli kartlar RSI, MACD, bantlar ve hacim gibi göstergeleri okunabilir dilde özetler. "
            "Günlük metin özeti aşağıdadır."
        )
        ig_txt.setObjectName("sectionSub")
        ig_txt.setWordWrap(True)
        igl.addWidget(ig_txt)
        left_l.addWidget(ind_guide)

        last = self._df.iloc[-1]
        close = float(last.get("Close", 0) or 0)
        open_p = float(last.get("Open", 0) or 0)
        day_ch = ((close - open_p) / open_p * 100.0) if open_p else 0.0
        vr = dh.safe_ratio(last.get("Volume"), self._df["Volume"].tail(30).mean())
        score = float(self._results.get("score", 0) or 0)

        hero = QHBoxLayout()
        sig = dh.signal_label_tr(self._results)
        anom = self._results.get("anomalies") or {}
        has_anom = bool(anom.get("has_anomaly"))
        hero.addWidget(
            self._header_tile("Güncel fiyat", f"{close:.2f} ₺", f"Günlük değişim {day_ch:+.2f}%", self._accent("green" if day_ch >= 0 else "red")),
            1,
        )
        hero.addWidget(
            self._header_tile("Ana sinyal", sig, f"Skor {score:.1f}/100", self._accent({"BUY": "green", "SELL": "red"}.get(self._results.get("signal", ""), "orange"))),
            1,
        )
        hero.addWidget(
            self._header_tile(
                "Anomali",
                "UYARI VAR" if has_anom else "TEMİZ",
                f"{len(anom.get('reasons') or [])} tetikleyici" if has_anom else "Belirgin sapma yok",
                self._accent("yellow" if has_anom else "green"),
            ),
            1,
        )
        hero.addWidget(
            self._header_tile("Hacim ritmi", f"{vr:.2f}×", "30 günlük ortalamaya göre", self._accent("green" if vr >= 1.5 else "orange" if vr >= 1.0 else "yellow")),
            1,
        )
        left_l.addLayout(hero)

        cards = dh.collect_indicator_cards(self._df, self._results)
        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(10)
        for idx, c in enumerate(cards):
            grid.addWidget(self._metric_card(c), idx // 2, idx % 2)
        left_l.addWidget(grid_w)

        narr = QFrame()
        narr.setObjectName("detailPanel")
        nl = QVBoxLayout(narr)
        nl.setContentsMargins(14, 12, 14, 12)
        nt = QLabel("Günlük teknik özet")
        nt.setObjectName("sectionTitle")
        nb = QLabel(dh.indicator_narrative(self._df, self._results))
        nb.setObjectName("sectionSub")
        nb.setWordWrap(True)
        nl.addWidget(nt)
        nl.addWidget(nb)
        left_l.addWidget(narr)

        main_l.addWidget(self._wrap_scroll(left_inner))
        return container

    def _start_news_fetch(self):
        self._news_thread = _NewsFetchThread(self._ticker_full, self._ticker_clean)
        t = self._news_thread
        t.setParent(self)
        t.done.connect(self._on_news_done)
        t.failed.connect(self._on_news_fail)
        t.finished.connect(self._on_news_thread_finished)
        t.finished.connect(t.deleteLater)
        t.start()

    def _on_news_thread_finished(self) -> None:
        # İş parçacığı bittiğinde pointer'ı temizle (kapanışta tekrar dokunmayalım).
        self._news_thread = None

    def _clear_news_layout(self):
        if not self._news_layout:
            return
        while self._news_layout.count():
            item = self._news_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_news_done(self, items: list):
        self._clear_news_layout()
        if not self._news_layout:
            return
        for news in items:
            card = QFrame()
            card.setObjectName("detailPanel")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            src = QLabel(news.get("source", ""))
            src.setObjectName("detailTileTitle")
            title = (news.get("title") or "")[:140]
            link = news.get("link") or ""
            safe_t = html.escape(title)
            safe_u = html.escape(link)
            tl = QLabel(f'<a href="{safe_u}">{safe_t}</a>')
            tl.setOpenExternalLinks(True)
            tl.setWordWrap(True)
            tl.setTextFormat(Qt.TextFormat.RichText)
            tl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            sum_ = (news.get("summary") or "")[:220]
            if len((news.get("summary") or "")) > 220:
                sum_ += "…"
            sl = QLabel(html.escape(sum_))
            sl.setObjectName("detailTileSub")
            sl.setWordWrap(True)
            cl.addWidget(src)
            cl.addWidget(tl)
            cl.addWidget(sl)
            self._news_layout.addWidget(card)
        self._news_layout.addStretch()

    def _on_news_fail(self, msg: str):
        self._clear_news_layout()
        if self._news_layout:
            self._news_layout.addWidget(QLabel(f"Haber hatası: {msg[:180]}"))
            self._news_layout.addStretch()

    def _build_news_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)
        outer.addWidget(
            self._section_header(
                "Haber panosu",
                f"{self._ticker_clean} — Yahoo Finance özet akışı; bağlantılar tarayıcıda açılır. Yatırım tavsiyesi değildir.",
            )
        )
        n_intro = QFrame()
        n_intro.setObjectName("detailPanel")
        nil = QVBoxLayout(n_intro)
        nil.setContentsMargins(12, 10, 12, 10)
        ni = QLabel(
            "Haberler ağ üzerinden yüklenir; gecikme veya boş liste normal olabilir. "
            "Ham fiyat/hacim verisi ve göstergeler «Ham veri» sekmesindedir."
        )
        ni.setObjectName("sectionSub")
        ni.setWordWrap(True)
        nil.addWidget(ni)
        outer.addWidget(n_intro)
        news_host = QWidget()
        self._news_layout = QVBoxLayout(news_host)
        self._news_layout.setSpacing(8)
        self._news_layout.addWidget(QLabel("Haberler yükleniyor…"))
        outer.addWidget(self._wrap_scroll(news_host), 1)
        return w

    def _build_anomaly_tab(self) -> QWidget:
        shell = QFrame()
        shell.setObjectName("detailAnomalyShell")
        sl = QVBoxLayout(shell)
        sl.setContentsMargins(12, 12, 12, 12)
        sl.setSpacing(14)

        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 0, 0)
        anomaly = self._results.get("anomalies") or {}
        direction = dh.anomaly_direction_label(self._results)
        reasons = anomaly.get("reasons") or []

        lay.addWidget(
            self._section_header(
                "Uyumsuzluk analizi",
                "Fiyat, hacim ve momentum birbirini tutmuyorsa model bunu uyarı olarak işaretler; yatırım tavsiyesi değildir.",
            )
        )

        explain = QFrame()
        explain.setObjectName("detailAnomalyIntro")
        el = QVBoxLayout(explain)
        el.setContentsMargins(16, 12, 16, 12)
        ex_h = QLabel("Nasıl okumalı?")
        ex_h.setObjectName("sectionTitle")
        el.addWidget(ex_h)
        ep = QLabel(
            "<b>Uyumsuzluk</b> burada, teknik göstergelerin aynı yönü desteklemediği veya birbiriyle çelişen sinyaller "
            "ürettiği durumları ifade eder (ör. fiyat yükselirken momentum zayıflıyor). "
            "<b>Şiddet</b> tetikleyicilerin sayısı ve türüne göre kabaca gruplanır; yüksek şiddet daha fazla dikkat "
            "isteyebileceği anlamına gelir, kesin zarar veya kazanç anlamına gelmez. "
            "<b>Yön</b>, mevcut skorun baskın olarak alım veya satış tarafına mı işaret ettiğini özetler."
        )
        ep.setObjectName("sectionSub")
        ep.setWordWrap(True)
        ep.setTextFormat(Qt.TextFormat.RichText)
        el.addWidget(ep)
        lay.addWidget(explain)

        hero = QHBoxLayout()
        sev = str(anomaly.get("severity", "none")).upper()
        hero.addWidget(
            self._header_tile("Bulunan uyumsuzluk", str(len(reasons)), "Aktif teknik alarm sayısı", self._accent("orange" if reasons else "green")),
            1,
        )
        hero.addWidget(self._header_tile("Şiddet", sev, dh.severity_caption(anomaly.get("severity")), self._accent("red" if sev == "HIGH" else "orange" if sev == "MEDIUM" else "yellow")), 1)
        hero.addWidget(self._header_tile("Yön", direction, "Skorun işaret ettiği baskın yön", self._accent("green")), 1)
        hero.addWidget(
            self._header_tile(
                "Durum",
                "Alarm aktif" if anomaly.get("has_anomaly") else "Temiz",
                f"{len(reasons)} tetikleyici" if anomaly.get("has_anomaly") else "Ek sapma yok",
                self._accent("yellow" if anomaly.get("has_anomaly") else "green"),
            ),
            1,
        )
        lay.addLayout(hero)

        ov = QFrame()
        ov.setObjectName("detailAnomalyOverview")
        ovl = QVBoxLayout(ov)
        ovl.setContentsMargins(16, 14, 16, 14)
        ovl.addWidget(QLabel("Bu hisse için özet görüş"))
        ovt = QLabel(dh.anomaly_overview_text(self._results, self._ticker_clean, direction))
        ovt.setWordWrap(True)
        ovt.setObjectName("sectionSub")
        ovl.addWidget(ovt)
        lay.addWidget(ov)

        blocks_fr = QFrame()
        blocks_fr.setObjectName("detailAnomalyBlocks")
        bl = QVBoxLayout(blocks_fr)
        bl.setContentsMargins(16, 14, 16, 14)
        bl.addWidget(QLabel("Tespit edilen başlıklar"))
        details = anomaly.get("details") or {}
        blocks = dh.anomaly_blocks(details)
        if blocks:
            for b in blocks:
                blk = QFrame()
                blk.setObjectName("detailTile")
                bv = QVBoxLayout(blk)
                bv.setContentsMargins(12, 10, 12, 10)
                bv.addWidget(QLabel(f"● {b['title']}"))
                d1 = QLabel(b["detail"])
                d1.setStyleSheet(f"color: {self._accent('orange')}; font-weight: 600;")
                d1.setWordWrap(True)
                bv.addWidget(d1)
                bv.addWidget(QLabel(b["description"]))
                bv.addWidget(QLabel(f"Yönetim notu: {b['management']}"))
                bl.addWidget(blk)
        else:
            bl.addWidget(
                QLabel(
                    "Bu hissede ek teknik uyumsuzluk tespit edilmedi. Fiyat, hacim ve momentum birbirini bozan bir alarm üretmiyor."
                )
            )
        lay.addWidget(blocks_fr)

        def bullet_panel(title: str, lines: list[str]) -> QFrame:
            f = QFrame()
            f.setObjectName("detailPanel")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 12, 16, 12)
            fl.addWidget(QLabel(title))
            for line in lines:
                fl.addWidget(QLabel(f"• {line}"))
            return f

        lay.addWidget(bullet_panel("Risk yönetimi yorumu", dh.anomaly_management_notes(anomaly)))
        lay.addWidget(bullet_panel("İşlem disiplini", dh.anomaly_discipline_notes(anomaly)))

        dec = QFrame()
        dec.setObjectName("detailAnomalyDecision")
        dl = QVBoxLayout(dec)
        dl.setContentsMargins(16, 14, 16, 14)
        dl.addWidget(QLabel("Karar özeti"))
        dec_lbl = QLabel(dh.decision_sentence(self._df, self._results, self._ticker_clean))
        dec_lbl.setWordWrap(True)
        dl.addWidget(dec_lbl)
        for item in dh.anomaly_action_items(anomaly):
            dl.addWidget(QLabel(f"• {item}"))
        dl.addWidget(QLabel("Bu özet işlem emri değildir; teknik risk farkındalığı içindir."))
        lay.addWidget(dec)
        lay.addStretch()

        scroll = self._wrap_scroll(inner)
        sl.addWidget(scroll)
        return shell

    def _build_summary_tab(self) -> QWidget:
        inner = QWidget()
        lay = QVBoxLayout(inner)
        if self._df.empty:
            lay.addWidget(QLabel("Veri yok"))
            return self._wrap_scroll(inner)

        last = self._df.iloc[-1]
        close = float(last["Close"])
        open_p = float(last.get("Open", 0) or 0)
        day_ch = ((close - open_p) / open_p * 100.0) if open_p else 0.0
        high = float(last["High"])
        low = float(last["Low"])
        volume = float(last["Volume"])
        avg_volume = float(self._df["Volume"].tail(30).mean())
        score = float(self._results.get("score", 0) or 0)

        lay.addWidget(
            self._section_header(
                "Karar özeti",
                "Güncel görünüm, puan dağılımı ve işlem öncesi hızlı değerlendirme.",
            )
        )

        def score_caption(sc: float) -> str:
            if sc >= 75:
                return "Güçlü teknik avantaj"
            if sc >= 60:
                return "Olumlu ama teyit isteyen yapı"
            if sc >= 40:
                return "Kararsız bölge"
            return "Zayıf teknik görünüm"

        def summary_rec() -> str:
            s = self._results.get("signal", "WAIT")
            if s == "BUY":
                return "Trend teyidi varsa izleme adayı"
            if s == "SELL":
                return "Baskı sürüyor; savunmacı kalın"
            return "Net yön yokken sabır tarafı güçlü"

        hero = QHBoxLayout()
        hero.addWidget(self._summary_tile("Teknik skor", f"{score:.1f}/100", score_caption(score), self._accent("green" if score >= 60 else "orange" if score >= 40 else "red")), 1)
        hero.addWidget(
            self._summary_tile("Fiyat ritmi", f"{day_ch:+.2f}%", f"Gün içi aralık {low:.2f} – {high:.2f} ₺", self._accent("green" if day_ch >= 0 else "red")),
            1,
        )
        hero.addWidget(
            self._summary_tile("İşlem tonu", dh.signal_label_tr(self._results), summary_rec(), self._accent({"BUY": "green", "SELL": "red"}.get(self._results.get("signal", ""), "orange"))),
            1,
        )
        lay.addLayout(hero)

        def _fmt_snap(x, nd: int = 2) -> str:
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return "—"
            return f"{float(x):.{nd}f}"

        rsi_raw = last.get("RSI")
        macdh = last.get("MACD_Hist")
        atr_v = last.get("ATR")
        atr_pct = None
        if atr_v is not None and not pd.isna(atr_v) and close:
            atr_pct = float(atr_v) / close * 100.0

        snap = QHBoxLayout()
        snap.addWidget(
            self._summary_tile("RSI (14)", _fmt_snap(rsi_raw), "Momentum; uç değerler dikkat gerektirir", self._accent("orange")),
            1,
        )
        mh = float(macdh) if macdh is not None and not pd.isna(macdh) else None
        snap.addWidget(
            self._summary_tile(
                "MACD histogram",
                _fmt_snap(macdh),
                "Sıfır çizgisine göre kısa güç",
                self._accent("green" if mh and mh > 0 else "red" if mh and mh < 0 else "yellow"),
            ),
            1,
        )
        snap.addWidget(
            self._summary_tile(
                "ATR / fiyat",
                f"{atr_pct:.2f}%" if atr_pct is not None else "—",
                "Günlük oynaklığın fiyata oranı",
                self._accent("yellow"),
            ),
            1,
        )
        lay.addLayout(snap)

        comp = QFrame()
        comp.setObjectName("detailPanel")
        cl = QVBoxLayout(comp)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.addWidget(QLabel("Model alt skorları (0–100)"))
        csub = QLabel(
            "Tarama motorundaki RSI, MACD, Bollinger, hacim ve SMA bileşenlerinin uyum puanları; "
            "tablodaki teknik skor bunların ağırlıklı birleşimidir."
        )
        csub.setObjectName("sectionSub")
        csub.setWordWrap(True)
        cl.addWidget(csub)
        rs_row = QHBoxLayout()
        for title, key in (
            ("RSI", "rsi_score"),
            ("MACD", "macd_score"),
            ("Bant", "bb_score"),
            ("Hacim", "volume_score"),
            ("SMA", "sma_score"),
        ):
            v = float(self._results.get(key, 0) or 0)
            rs_row.addWidget(
                self._summary_tile(title, f"{v:.0f}", "Bileşen", self._accent("green" if v >= 60 else "orange" if v >= 40 else "red")),
                1,
            )
        cl.addLayout(rs_row)
        lay.addWidget(comp)

        sector = self._results.get("sector") or self._results.get("Sector")
        trend_l = self._results.get("trend_label")
        if sector or trend_l:
            meta = QHBoxLayout()
            if sector:
                meta.addWidget(self._summary_tile("Sektör", str(sector), "Tarama evreninden", self._accent("blue")), 1)
            if trend_l:
                meta.addWidget(self._summary_tile("Trend etiketi", str(trend_l), "Hareketli ortalama yapısı", self._accent("green")), 1)
            lay.addLayout(meta)

        mini = QHBoxLayout()
        for label, val, colk in [
            ("Güncel", f"{close:.2f} ₺", "green"),
            ("Açılış", f"{open_p:.2f} ₺", "green"),
            ("Hacim", f"{int(volume):,}", "orange"),
            ("30G ort.", f"{int(avg_volume):,}", "yellow"),
        ]:
            mini.addWidget(self._summary_tile(label, val, "", self._accent(colk)))
        lay.addLayout(mini)

        sum_intro = QFrame()
        sum_intro.setObjectName("detailPanel")
        sil = QVBoxLayout(sum_intro)
        sil.setContentsMargins(14, 12, 14, 12)
        sil.addWidget(QLabel("Özet sekmesi"))
        sit = QLabel(
            "Aşağıdaki kartlar güncel fiyat davranışı ve model tonunu bir cümlelik özetlerle birleştirir. "
            "En alttaki metin kutusu tarama sonuçlarından gelen gerekçe ve getiri satırlarını toplar."
        )
        sit.setObjectName("sectionSub")
        sit.setWordWrap(True)
        sil.addWidget(sit)
        lay.addWidget(sum_intro)

        health = QFrame()
        health.setObjectName("detailPanel")
        hl = QVBoxLayout(health)
        hl.setContentsMargins(14, 12, 14, 12)
        hl.addWidget(QLabel("Teknik dağılım"))
        hcap = QLabel(
            "Her satır 0–100 ölçeğinde bir teknik uyum puanı gösterir; çubuk uzunluğu puanla orantılıdır "
            "(ör. 55 yaklaşık %55 dolu). Renkler göreli güçlü (yeşil), orta (turuncu) ve zayıf (kırmızı) ayrımı içindir."
        )
        hcap.setObjectName("sectionSub")
        hcap.setWordWrap(True)
        hl.addWidget(hcap)
        track_bg = "#1c2633" if self._dark else "#dce4ef"
        for title, val, cname in dh.summary_components(self._df, self._results):
            row = QHBoxLayout()
            row.addWidget(QLabel(title), 1)
            pct = int(round(max(0.0, min(100.0, val))))
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(pct)
            pb.setTextVisible(False)
            pb.setFixedHeight(14)
            pb.setMinimumWidth(180)
            acol = self._accent(cname)
            pb.setStyleSheet(
                f"QProgressBar {{ border: none; background-color: {track_bg}; border-radius: 6px; }}"
                f"QProgressBar::chunk {{ background-color: {acol}; border-radius: 6px; }}"
            )
            row.addWidget(pb, 2)
            row.addWidget(QLabel(f"{val:.0f}/100"))
            hl.addLayout(row)
        lay.addWidget(health)

        two = QHBoxLayout()
        notes_l = QFrame()
        notes_l.setObjectName("detailPanel")
        nll = QVBoxLayout(notes_l)
        nll.setContentsMargins(12, 10, 12, 10)
        nll.addWidget(QLabel("Hızlı notlar"))
        for n in dh.summary_notes_list(self._df, self._results):
            lb = QLabel(f"• {n}")
            lb.setWordWrap(True)
            nll.addWidget(lb)
        disc = QFrame()
        disc.setObjectName("detailPanel")
        dl = QVBoxLayout(disc)
        dl.setContentsMargins(12, 10, 12, 10)
        dl.addWidget(QLabel("İşlem disiplini"))
        for n in dh.discipline_notes_list(self._results):
            lb = QLabel(f"• {n}")
            lb.setWordWrap(True)
            dl.addWidget(lb)
        two.addWidget(notes_l, 1)
        two.addWidget(disc, 1)
        lay.addLayout(two)

        rationale = QTextEdit()
        rationale.setReadOnly(True)
        rationale.setFont(QFont("Segoe UI", 11))
        rationale.setPlaceholderText("Tarama özeti ve gerekçe satırları burada listelenir.")
        lines = [
            f"Sembol: {self._ticker_full}",
            "",
            f"Özet satırı: {self._results.get('thesis', '—')}",
            "",
            "Fırsat ve gerekçe:",
            build_opportunity_rationale({**self._results, "symbol": self._ticker_clean}),
        ]
        b = self._results.get("benchmark_20d_note")
        if b is not None:
            lines.extend(["", f"BIST 100 referans ~20 işlem günü getiri: {b:+.2f}%"])
        p5 = self._results.get("pct_5d")
        p60 = self._results.get("pct_60d")
        if p5 is not None or p60 is not None:
            lines.append("")
            if p5 is not None:
                lines.append(f"5 gün getiri: {p5:+.2f}%")
            if p60 is not None:
                lines.append(f"60 gün getiri: {p60:+.2f}%")
        an = self._results.get("anomalies") or {}
        if an.get("reasons"):
            lines.extend(["", "Anomali etiketleri: " + ", ".join(an["reasons"])])
        if not self._results:
            lines = ["Bu sembol için tarama özeti yok; önce tam tarama yapın.", "", "Ham veri ve grafik yine de görüntülenir."]
        rationale.setPlainText("\n".join(lines))
        lay.addWidget(rationale)

        bottom = QFrame()
        bottom.setObjectName("detailPanel")
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(14, 12, 14, 12)
        bl.addWidget(QLabel("Karar cümlesi"))
        cs = QLabel(dh.decision_sentence(self._df, self._results, self._ticker_clean))
        cs.setWordWrap(True)
        bl.addWidget(cs)
        lay.addWidget(bottom)

        scroll = self._wrap_scroll(inner)
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.addWidget(scroll)
        return wrap

    def _raw_column_order(self) -> list[str]:
        df = self._df
        first = ["Open", "High", "Low", "Close", "Volume"]
        out: list[str] = []
        for c in first:
            if c in df.columns:
                out.append(c)
        for c in _NUM_COLS:
            if c in df.columns and c not in out:
                out.append(c)
        for c in df.columns:
            if str(c) not in out:
                out.append(str(c))
        return out

    @staticmethod
    def _fmt_raw_cell(col: str, val) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        if col == "Volume":
            try:
                return f"{int(float(val)):,}"
            except (TypeError, ValueError):
                return str(val)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if isinstance(val, float):
                t = f"{val:.6f}".rstrip("0").rstrip(".")
                return t if t else "0"
            return str(int(val))
        return str(val)

    def _refresh_raw_table(self):
        tbl = self._raw_table
        df = self._df
        if tbl is None or df is None or df.empty:
            return
        n = min(self._raw_days.value(), len(df))
        n = max(1, n)
        tail = df.tail(n).iloc[::-1]
        cols = self._raw_column_order()
        tbl.clear()
        tbl.setColumnCount(len(cols) + 1)
        tbl.setHorizontalHeaderLabels(["Tarih"] + cols)
        tbl.setRowCount(len(tail))
        hdr = tbl.horizontalHeader()
        hdr.setMinimumSectionSize(56)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for c in range(1, tbl.columnCount()):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Interactive)
        tbl.setAlternatingRowColors(True)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(True)

        for ri, (ix, row) in enumerate(tail.iterrows()):
            if hasattr(ix, "strftime"):
                date_s = ix.strftime("%Y-%m-%d")
            else:
                date_s = str(ix)[:10]
            it0 = QTableWidgetItem(date_s)
            it0.setFlags(it0.flags() ^ Qt.ItemFlag.ItemIsEditable)
            it0.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            tbl.setItem(ri, 0, it0)
            for ci, col in enumerate(cols, start=1):
                raw = row.get(col)
                txt = self._fmt_raw_cell(col, raw)
                cell = QTableWidgetItem(txt)
                cell.setFlags(cell.flags() ^ Qt.ItemFlag.ItemIsEditable)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tbl.setItem(ri, ci, cell)

        tips_raw = ["İşlem tarihi (en yeni üstte)."] + [
            {
                "Open": "Gün içi açılış fiyatı.",
                "High": "Gün içi en yüksek.",
                "Low": "Gün içi en düşük.",
                "Close": "Kapanış fiyatı.",
                "Volume": "İşlem hacmi (adet).",
                "RSI": "14 periyot RSI.",
                "MACD": "MACD çizgisi.",
                "MACD_Signal": "MACD sinyal çizgisi.",
                "MACD_Hist": "MACD histogram.",
                "ATR": "Ortalama true range.",
            }.get(c, f"{_COL_TR.get(c, c)} sütunu.")
            for c in cols
        ]
        for ci in range(tbl.columnCount()):
            hi = tbl.horizontalHeaderItem(ci)
            if hi is not None and ci < len(tips_raw):
                hi.setToolTip(tips_raw[ci])

    def _export_raw_csv_slot(self) -> None:
        df = self._df
        if df is None or df.empty or self._raw_days is None:
            QMessageBox.warning(self, _APP_NAME, "Dışa aktarılacak veri yok.")
            return
        n = min(int(self._raw_days.value()), len(df))
        n = max(1, n)
        last_ix = df.index[-1]
        suggested = ac.suggested_raw_ohlc_csv_filename(self._ticker_clean, n, last_ix)
        default_path = str(Path.home() / suggested)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Ham veriyi CSV olarak kaydet",
            default_path,
            "CSV (*.csv)",
        )
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".csv":
            p = p.with_suffix(".csv")
        try:
            tail = df.tail(n).iloc[::-1]
            cols = self._raw_column_order()
            sub = tail[cols].copy()
            dates = []
            for ix in sub.index:
                if hasattr(ix, "strftime"):
                    dates.append(ix.strftime("%Y-%m-%d"))
                else:
                    dates.append(str(ix)[:10])
            sub.insert(0, "Tarih", dates)
            sub.to_csv(p, index=False, encoding="utf-8-sig")
        except Exception as exc:
            logger.exception("Ham veri CSV")
            QMessageBox.critical(self, _APP_NAME, f"CSV kaydedilemedi:\n{exc}")

    def _build_raw_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        if self._df is None or self._df.empty:
            outer.addWidget(QLabel("Ham veri yok; tablo oluşturulamadı."))
            self._raw_table = None
            self._raw_days = None
            return w
        top = QHBoxLayout()
        top.addWidget(
            QLabel(
                "Son işlem günleri (en yeni üstte). Fiyat/hacim ve hesaplanan göstergeler; yatay kaydırma ile tüm sütunlar."
            ),
            1,
        )
        top.addWidget(QLabel("Gün sayısı:"))
        self._raw_days = QSpinBox()
        n_all = len(self._df)
        self._raw_days.setRange(1, max(1, n_all))
        self._raw_days.setValue(min(30, n_all))
        self._raw_days.setToolTip("Gösterilecek ve CSV’ye yazılacak son işlem günü sayısı (en yeni üstte).")
        top.addWidget(self._raw_days)
        btn_csv = QPushButton("CSV dışa aktar")
        btn_csv.setToolTip("Seçilen gün sayısı kadar satırı UTF-8 CSV olarak kaydeder.")
        btn_csv.clicked.connect(self._export_raw_csv_slot)
        top.addWidget(btn_csv)
        outer.addLayout(top)
        self._raw_table = QTableWidget()
        self._raw_days.valueChanged.connect(self._refresh_raw_table)
        outer.addWidget(self._raw_table, 1)
        self._refresh_raw_table()
        return w


DetailDialog = DetailView
