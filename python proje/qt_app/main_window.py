# -*- coding: utf-8 -*-
"""Ana pencere — tarama, sonuçlar, fırsatlar, günlük hareketler."""

from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

import pandas as pd
from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nyron.core.analyzer import StockAnalyzer
from nyron.core import controller as ac
from config import BENCHMARK, SCREEN, UI, UNIVERSE
from nyron.core.favorites import FavoritesStore
from nyron.core.metrics import (
    build_opportunity_rationale,
    build_opportunity_why_for_user,
    build_thesis_line,
)
from qt_app import branding
from qt_app import ui_icons as nui
from qt_app.finance_glossary import apply_glossary_browser_style, build_glossary_widget
from qt_app.styles import stylesheet_dark, stylesheet_light
from qt_app.worker import AnalysisWorker

logger = logging.getLogger(__name__)

_APP_NAME = branding.APP_NAME

# Fırsatlar üst bandı: kısa, motive edici borsa alıntıları (Türkçe, kaynak kişi)
_NYRON_MARKET_QUOTES: list[tuple[str, str]] = [
    (
        "Borsada sabır, en az sermaye kadar değerlidir; acele her zaman bedel ödetir.",
        "Warren Buffett",
    ),
    (
        "Hiçbir şey yapmayan yatırımcıdan daha cesur olan yoktur; sürekli işlem çoğu zaman masraftır.",
        "Peter Lynch",
    ),
    (
        "Kısa vadede borsa bir oy makinesi gibi görünür; uzun vadede ise bir tartıdır.",
        "Benjamin Graham",
    ),
    (
        "Risk, ne yaptığını bilmediğinde ortaya çıkar; önce anlayış, sonra pozisyon.",
        "Warren Buffett",
    ),
    (
        "Planınız yoksa, başkasının planında figüran olursunuz.",
        "Jim Rohn",
    ),
    (
        "Duygularını yönetemeyen yatırımcı, piyasanın oyuncağı olur.",
        "Paul Tudor Jones",
    ),
    (
        "Çeşitlendirme, cehalet için bir koruma sağlar; bildiğiniz alanda odaklanmak başka bir disiplindir.",
        "Warren Buffett",
    ),
    (
        "Piyasada para kazanmanın sırrı: korku ve açgözlülükten uzak durmaktır.",
        "Warren Buffett",
    ),
    (
        "Fiyat sizin ödediğinizdir; değer ise elde ettiğinizdir. İkisini karıştırmayın.",
        "Warren Buffett",
    ),
    (
        "Bu sefer farklıdır demek, yatırımda işittiğimiz en tehlikeli dört kelimedir.",
        "Sir John Templeton",
    ),
    (
        "Büyük servetler genelde sabırla birikir; bir gecede değil, yıllar içinde oluşur.",
        "Charlie Munger",
    ),
    (
        "Trend sizin dostunuzdur; ama her dalganın sizi kıyıya atmayacağını unutmayın.",
        "Ed Seykota",
    ),
    (
        "Disiplin, stratejiden daha nadiren başarısız olur.",
        "Ray Dalio",
    ),
    (
        "Kaybetmeyi göze almadığınız parayla asla oynamayın.",
        "Paul Samuelson",
    ),
]


class _LogBridge(QObject):
    """Çalışan iş parçacığı loglarını GUI iş parçacığına aktarır (QTextEdit'e doğrudan dokunma yok)."""

    append_line = Signal(str)


class _QtLogHandler(logging.Handler):
    def __init__(self, bridge: _LogBridge):
        super().__init__()
        self._bridge = bridge
        fmt = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s", "%H:%M:%S")
        self.setFormatter(fmt)

    def emit(self, record):
        try:
            self._bridge.append_line.emit(self.format(record))
        except Exception:
            self.handleError(record)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_APP_NAME)
        self.resize(UI.get("window_width", 1240), UI.get("window_height", 780))

        self._dark = True
        self._apply_stylesheet()

        self._analyzer = StockAnalyzer()
        self._results: list = []
        self._filtered: list = []
        self._all_data: dict = {}
        self._results_dict: dict = {}
        self._fav_store = FavoritesStore()
        self._favorites: set[str] = self._fav_store.load()
        self._worker: AnalysisWorker | None = None
        self._buy_rows_by_symbol: dict[str, dict] = {}
        self._brand_logo_lbl: QLabel | None = None

        central = QWidget()
        central.setObjectName("centralRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        self._chip_market_l = QLabel("Hazır")
        self._chip_market_l.setObjectName("chipValue")
        self._chip_scan_l = QLabel("—")
        self._chip_scan_l.setObjectName("chipValue")
        self._chip_bench_l = QLabel("—")
        self._chip_bench_l.setObjectName("chipValue")
        self._chip_universe_l = QLabel(UNIVERSE.get("name", "BIST 500"))
        self._chip_universe_l.setObjectName("chipValue")
        self._chip_universe_l.setToolTip(
            "Varsayılan evren BIST 500 (XU500). Özel liste için `data/stocks.txt` dosyasını doldurabilirsiniz."
        )

        hero_bar = QFrame()
        hero_bar.setObjectName("scanHeroBar")
        self._scan_hero_bar = hero_bar
        hero_outer = QHBoxLayout(hero_bar)
        hero_outer.setContentsMargins(18, 16, 18, 16)
        hero_outer.setSpacing(16)

        self._hero_chip_frames: list[QFrame] = []

        def _status_chip(caption: str, value_lbl: QLabel) -> QFrame:
            f = QFrame()
            f.setObjectName("statusChip")
            vl = QVBoxLayout(f)
            vl.setContentsMargins(10, 8, 10, 8)
            vl.setSpacing(4)
            vl.addStretch(1)
            cap = QLabel(caption)
            cap.setObjectName("chipTitle")
            cap.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            cap.setWordWrap(True)
            vl.addWidget(cap, 0, Qt.AlignmentFlag.AlignHCenter)
            vl.addWidget(value_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
            vl.addStretch(1)
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            value_lbl.setWordWrap(True)
            self._hero_chip_frames.append(f)
            return f

        titles_col = QWidget()
        titles_col.setFixedWidth(168)
        titles_col.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        tcl = QVBoxLayout(titles_col)
        tcl.setContentsMargins(8, 0, 8, 0)
        tcl.setSpacing(4)
        # Kicker: keep it brand-only (avoid index label noise).
        kicker = QLabel(f"{_APP_NAME.upper()}")
        kicker.setObjectName("heroKicker")
        kicker.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title = QLabel("Teknik tarama")
        title.setObjectName("heroTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sub = QLabel(
            "BIST 500 evrenini tara, filtrele, fırsatları incele. Çift tık ile hisse detayına geç."
        )
        sub.setObjectName("heroSub")
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        tcl.addWidget(kicker, 0, Qt.AlignmentFlag.AlignHCenter)
        tcl.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)
        tcl.addWidget(sub, 0, Qt.AlignmentFlag.AlignHCenter)

        self._hero_left_wrap = QWidget()
        self._hero_left_wrap.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        left_head = QHBoxLayout(self._hero_left_wrap)
        left_head.setContentsMargins(0, 0, 0, 0)
        left_head.setSpacing(14)
        self._brand_logo_lbl = self._make_brand_logo_label()
        if self._brand_logo_lbl is not None:
            left_head.addWidget(self._brand_logo_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        left_head.addWidget(titles_col, 0, Qt.AlignmentFlag.AlignVCenter)
        _logo_extra = 66 if self._brand_logo_lbl is not None else 0
        self._hero_left_wrap.setFixedWidth(_logo_extra + 168)

        self._hero_quote_slot = QWidget()
        self._hero_quote_slot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        qslot_lay = QHBoxLayout(self._hero_quote_slot)
        qslot_lay.setContentsMargins(0, 0, 0, 0)
        qslot_lay.setSpacing(0)
        qslot_lay.addStretch(1)

        self._hero_quote_card = QFrame()
        self._hero_quote_card.setObjectName("heroQuoteCard")
        self._hero_quote_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        cv = QVBoxLayout(self._hero_quote_card)
        cv.setContentsMargins(14, 12, 14, 12)
        cv.setSpacing(6)
        self._hero_quote_text = QLabel()
        self._hero_quote_text.setObjectName("heroQuoteText")
        self._hero_quote_text.setWordWrap(True)
        self._hero_quote_text.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._hero_quote_author = QLabel()
        self._hero_quote_author.setObjectName("heroQuoteAuthor")
        self._hero_quote_author.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        cv.addStretch(1)
        cv.addWidget(self._hero_quote_text)
        cv.addWidget(self._hero_quote_author)
        cv.addStretch(1)

        qslot_lay.addWidget(self._hero_quote_card, 0, Qt.AlignmentFlag.AlignVCenter)
        qslot_lay.addStretch(1)

        chips_outer = QWidget()
        chips_outer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        col_chips = QVBoxLayout(chips_outer)
        col_chips.setContentsMargins(0, 0, 0, 0)
        chips_row_w = QWidget()
        self._hero_chips_row_w = chips_row_w
        chips_h = QHBoxLayout(chips_row_w)
        chips_h.setSpacing(10)
        chips_h.setContentsMargins(0, 0, 0, 0)
        chips_h.addWidget(_status_chip("Durum", self._chip_market_l))
        chips_h.addWidget(_status_chip("Son tarama", self._chip_scan_l))
        _bench_cap = BENCHMARK.get("ui_chip_caption") or BENCHMARK.get("ticker", "Endeks")
        chips_h.addWidget(_status_chip(_bench_cap, self._chip_bench_l))
        self._chip_bench_l.setToolTip(
            "Referans endeks yaklaşık 20 işlem günü getirisi; tablolarda göreli güç ile karşılaştırma içindir."
        )
        chips_h.addWidget(_status_chip("Evren", self._chip_universe_l))
        col_chips.addStretch(1)
        col_chips.addWidget(chips_row_w, 0, Qt.AlignmentFlag.AlignVCenter)
        col_chips.addStretch(1)
        self._hero_chips_outer = chips_outer

        hero_outer.addWidget(self._hero_left_wrap, 0, Qt.AlignmentFlag.AlignVCenter)
        hero_outer.addWidget(self._hero_quote_slot, 1, Qt.AlignmentFlag.AlignVCenter)
        hero_outer.addWidget(chips_outer, 0, Qt.AlignmentFlag.AlignVCenter)

        self._hero_quote_last_idx = random.randrange(len(_NYRON_MARKET_QUOTES))
        self._hero_quote_timer = QTimer(self)
        self._hero_quote_timer.setInterval(5 * 60 * 1000)
        self._hero_quote_timer.timeout.connect(self._rotate_hero_quote)
        self._hero_quote_timer.start()

        # Üst aksiyonlar (eski araç çubuğu satırının yerine).
        # Aksiyonları Nyron başlık alanına yakın tutarak daha modern bir deneyim hedeflenir.
        actions = QFrame()
        actions.setObjectName("topActionsBar")
        actions_l = QHBoxLayout(actions)
        actions_l.setContentsMargins(14, 10, 14, 10)
        actions_l.setSpacing(10)

        left_actions = QWidget()
        left_actions.setObjectName("topActionsLeft")
        la = QHBoxLayout(left_actions)
        la.setContentsMargins(0, 0, 0, 0)
        la.setSpacing(8)

        mid_progress = QWidget()
        mid_progress.setObjectName("topActionsProgress")
        mp = QHBoxLayout(mid_progress)
        mp.setContentsMargins(0, 0, 0, 0)
        mp.setSpacing(8)

        right_actions = QWidget()
        right_actions.setObjectName("topActionsRight")
        ra = QHBoxLayout(right_actions)
        ra.setContentsMargins(0, 0, 0, 0)
        ra.setSpacing(6)

        # Araç düğmeleri (eski toolbar’dan taşındı)
        self._btn_run = QPushButton("Tarama başlat")
        self._btn_run.setObjectName("primary")
        self._btn_run.clicked.connect(self._start_scan)
        self._btn_cont = QPushButton("Sonuçlara geç")
        self._btn_cont.setObjectName("accent")
        self._btn_cont.setToolTip("Tarama tamamlanınca görünür.")
        self._btn_cont.hide()
        self._btn_cont.clicked.connect(self._show_results_view)
        self._btn_refresh = QPushButton("Yeniden tara")
        self._btn_refresh.hide()
        self._btn_refresh.clicked.connect(self._reset_scan)
        self._btn_csv = QPushButton("CSV dışa aktar")
        self._btn_csv.setToolTip("Şu anki filtrelenmiş tabloyu UTF-8 CSV olarak kaydeder.")
        self._btn_csv.hide()
        self._btn_csv.clicked.connect(self._export_csv_slot)
        self._btn_theme = QPushButton()
        self._btn_theme.setObjectName("iconToolButton")
        self._btn_theme.clicked.connect(self._toggle_theme)
        self._btn_quit = QPushButton()
        self._btn_quit.setObjectName("iconToolButton")
        self._btn_quit.clicked.connect(self.close)
        self._prog_lbl = QLabel("")
        self._prog_lbl.setObjectName("muted")
        self._prog = QProgressBar()
        self._prog.setRange(0, 100)
        self._prog.setValue(0)
        # Smooth progress animation (prevents jumpy bar updates).
        self._prog_target = 0
        self._prog_timer = QTimer(self)
        self._prog_timer.setInterval(25)
        self._prog_timer.timeout.connect(self._tick_progress_animation)

        la.addWidget(self._btn_run)
        la.addWidget(self._btn_cont)
        la.addWidget(self._btn_refresh)
        la.addWidget(self._btn_csv)

        mp.addWidget(self._prog_lbl)
        mp.addWidget(self._prog, 1)

        ra.addWidget(self._btn_theme)
        ra.addWidget(self._btn_quit)

        actions_l.addWidget(left_actions, 0)
        actions_l.addWidget(mid_progress, 1)
        actions_l.addWidget(right_actions, 0)

        hero_col = QWidget()
        hero_col.setObjectName("heroCol")
        self._hero_col = hero_col
        hero_col_l = QVBoxLayout(hero_col)
        hero_col_l.setContentsMargins(0, 0, 0, 0)
        hero_col_l.setSpacing(10)
        hero_col_l.addWidget(hero_bar)
        hero_col_l.addWidget(actions)
        root.addWidget(hero_col)

        self._apply_toolbar_action_icons()

        self._stack = QStackedWidget()
        # 0: log
        log_w = QWidget()
        log_l = QVBoxLayout(log_w)
        log_l.setSpacing(12)
        welcome = QFrame()
        welcome.setObjectName("welcomeCard")
        wl = QVBoxLayout(welcome)
        wl.setContentsMargins(18, 16, 18, 16)
        wl.setSpacing(8)
        w_title = QLabel("Nasıl ilerleyeceksiniz?")
        w_title.setObjectName("welcomeTitle")
        w_body = QLabel(
            "<b>1.</b> <b>Tarama başlat</b> ile BIST 500 (XU500) bileşenleri için veri alınır ve göstergeler hesaplanır.<br>"
            "<b>2.</b> İlerleme bu günlükte görünür; işlem bitince <b>Sonuçlara geç</b> düğmesi çıkar.<br>"
            "<b>3.</b> Sonuç ekranında tablolar, filtreler, metin araması ve CSV dışa aktarma kullanılabilir. "
            "Satıra çift tıklayınca hisse detayı uygulama içinde açılır; detayda sekme çubuğunun sağındaki <b>Geri</b> (tema ve çıkış ile aynı satır) ile sonuçlara dönersiniz."
        )
        w_body.setObjectName("welcomeBody")
        w_body.setWordWrap(True)
        w_body.setTextFormat(Qt.TextFormat.RichText)
        wl.addWidget(w_title)
        wl.addWidget(w_body)
        log_l.addWidget(welcome)
        log_hdr = QLabel("Tarama günlüğü")
        log_hdr.setObjectName("sectionTitle")
        self._log = QTextEdit()
        self._log.setObjectName("scanLog")
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 11))
        log_l.addWidget(log_hdr)
        log_l.addWidget(self._log, 1)
        self._stack.addWidget(log_w)

        # 1: sonuçlar
        res_w = QWidget()
        res_l = QVBoxLayout(res_w)
        self._tabs = QTabWidget()
        self._build_tab_all()
        self._build_tab_opportunities()
        self._build_tab_movers()
        self._build_tab_favorites()
        self._tab_glossary, self._glossary_browser = build_glossary_widget(self, self._dark)
        self._tabs.addTab(self._tab_all, "Tüm sonuçlar")
        self._tabs.addTab(self._tab_opp, "Fırsatlar")
        self._tabs.addTab(self._tab_mov, "Günün hareketleri")
        self._tabs.addTab(self._tab_fav, "Favoriler")
        self._tabs.addTab(self._tab_glossary, "Terimler rehberi")
        res_l.addWidget(self._tabs)
        self._stack.addWidget(res_w)

        self._embedded_detail = None
        self._detail_page = QWidget()
        dp_lay = QVBoxLayout(self._detail_page)
        dp_lay.setContentsMargins(0, 0, 0, 0)
        dp_lay.setSpacing(0)
        self._detail_holder = QWidget()
        self._detail_holder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._detail_holder_lay = QVBoxLayout(self._detail_holder)
        self._detail_holder_lay.setContentsMargins(0, 0, 0, 0)
        dp_lay.addWidget(self._detail_holder, 1)
        self._stack.addWidget(self._detail_page)

        root.addWidget(self._stack, 1)
        self._stack.currentChanged.connect(self._on_main_stack_changed)

        self._tabs.currentChanged.connect(self._on_results_tab_changed)
        self._refresh_opp_hero_quote()

        self._log_bridge = _LogBridge(self)
        self._log_bridge.append_line.connect(self._log.append, Qt.ConnectionType.QueuedConnection)
        rlog = logging.getLogger()
        if not any(isinstance(h, _QtLogHandler) for h in rlog.handlers):
            qh = _QtLogHandler(self._log_bridge)
            qh.setLevel(logging.INFO)
            rlog.addHandler(qh)

        self._apply_hero_quote_index(self._hero_quote_last_idx)
        self._sync_responsive_layout()
        self._on_main_stack_changed(self._stack.currentIndex())

    def _apply_toolbar_action_icons(self) -> None:
        self._refresh_all_action_icons()

    def _refresh_all_action_icons(self) -> None:
        d = self._dark
        if hasattr(self, "_btn_quit") and self._btn_quit is not None:
            self._btn_quit.setIcon(nui.icon_close(d))
            self._btn_quit.setText("")
            self._btn_quit.setToolTip("Çıkış")
        self._refresh_theme_toggle_icons()

    def _refresh_theme_toggle_icons(self) -> None:
        if self._dark:
            ic, tip = nui.icon_theme_to_light(), "Aydınlık temaya geç"
        else:
            ic, tip = nui.icon_theme_to_dark(), "Karanlık temaya geç"
        if hasattr(self, "_btn_theme") and self._btn_theme is not None:
            self._btn_theme.setIcon(ic)
            self._btn_theme.setText("")
            self._btn_theme.setToolTip(tip)

    def _on_main_stack_changed(self, index: int) -> None:
        # 0: scan log, 1: results, 2: embedded detail
        hero_visible = index in (0, 1)
        self._scan_hero_bar.setVisible(index == 0)
        hc = getattr(self, "_hero_col", None)
        if hc is not None:
            hc.setVisible(hero_visible)

    def _teardown_embedded_detail(self) -> None:
        w = getattr(self, "_embedded_detail", None)
        if w is None:
            return
        w.shutdown_async()
        self._detail_holder_lay.removeWidget(w)
        w.deleteLater()
        self._embedded_detail = None

    def _close_detail_embedded(self) -> None:
        self._teardown_embedded_detail()
        self._stack.setCurrentIndex(1)
        self.setWindowTitle(_APP_NAME)

    def _apply_stylesheet(self):
        self.setStyleSheet(stylesheet_dark() if self._dark else stylesheet_light())

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._sync_responsive_layout()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_responsive_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_responsive_layout()

    def _layout_expanded(self) -> bool:
        st = self.windowState()
        return bool(st & Qt.WindowState.WindowMaximized) or bool(st & Qt.WindowState.WindowFullScreen)

    def _sync_responsive_layout(self) -> None:
        self._adjust_buy_why_panel_width()
        self._adjust_hero_layout()
        self._adjust_opp_hero_layout()

    def _adjust_buy_why_panel_width(self) -> None:
        fr = getattr(self, "_why_fr_buy", None)
        if fr is None:
            return
        maximized = self._layout_expanded()
        w = self.width()
        if maximized:
            target = int(min(720, max(420, w * 0.34)))
            fr.setMinimumWidth(max(280, target - 60))
            fr.setMaximumWidth(target)
        else:
            fr.setMinimumWidth(220)
            fr.setMaximumWidth(320)

    @staticmethod
    def _hero_quote_font_sizes(cw: int, ch: int, quote_visible: str) -> tuple[int, int]:
        usable_h = max(24.0, float(ch - 48))
        usable_w = max(72.0, float(cw - 24))
        for fs in range(14, 8, -1):
            font = QFont()
            font.setPointSize(fs)
            font.setFamilies(["Segoe UI", "Tahoma", "sans-serif"])
            doc = QTextDocument()
            doc.setDefaultFont(font)
            doc.setPlainText(quote_visible)
            doc.setTextWidth(usable_w)
            if doc.size().height() <= usable_h:
                return fs, max(9, fs - 2)
        return 8, 9

    def _adjust_hero_layout(self) -> None:
        card = getattr(self, "_hero_quote_card", None)
        hb = getattr(self, "_scan_hero_bar", None)
        left_w = getattr(self, "_hero_left_wrap", None)
        if card is None or hb is None or left_w is None:
            return

        mx = self._layout_expanded()
        bw = hb.width()
        if bw < 80:
            bw = max(520, min(1600, int(self.width() * 0.97))) if self.width() > 120 else 900

        inner = max(0, bw - 36)
        lw = left_w.width() if left_w.width() > 1 else left_w.minimumWidth()
        remaining = max(1, inner - lw - 32)

        min_quote_w, min_chip = 100, 56
        chip_w = min_chip
        chips_w = 4 * chip_w + 30
        cw = remaining - chips_w
        for try_w in range(126, min_chip - 1, -2):
            _row = 4 * try_w + 30
            _cw = remaining - _row
            if _cw >= min_quote_w:
                chip_w = try_w
                chips_w = _row
                cw = _cw
                break
        else:
            cw = max(72, remaining - chips_w)

        max_quote = min(520, max(220, int(bw * 0.40)))
        cw = min(int(cw), max_quote)

        ch = 148 if mx else 128
        quote_txt = self._hero_quote_text.text() or "«»"
        fs_q, fs_a = self._hero_quote_font_sizes(int(cw), int(ch), quote_txt)
        if mx:
            fs_q = min(fs_q, 14)
            fs_a = min(fs_a, 12)
        else:
            fs_q = min(fs_q, 12)
            fs_a = min(fs_a, 11)

        card.setMinimumWidth(int(cw))
        card.setMaximumWidth(int(cw))
        card.setFixedHeight(int(ch))

        if self._dark:
            tcol, acol = "#d8e4ef", "#a8c4df"
        else:
            tcol, acol = "#0f172a", "#475569"
        self._hero_quote_text.setStyleSheet(
            f"color: {tcol}; font-size: {fs_q}pt; line-height: 1.35; font-weight: 500;"
        )
        self._hero_quote_author.setStyleSheet(f"color: {acol}; font-size: {fs_a}pt; font-weight: 600;")

        for chip_fr in getattr(self, "_hero_chip_frames", []):
            chip_fr.setFixedSize(int(chip_w), int(ch))

        row = getattr(self, "_hero_chips_row_w", None)
        if row is not None:
            row.setFixedWidth(int(chips_w))

    def _adjust_opp_hero_layout(self) -> None:
        oq = getattr(self, "_opp_hero_quote", None)
        if oq is None:
            return
        mx = self._layout_expanded()
        tw = self.width() if self.width() > 200 else 960
        max_w = min(520, max(260, int(tw * 0.38)))
        oq.setFixedWidth(int(max_w))
        box_h = 132 if mx else 108
        raw = (oq.text() or "«»").replace("\n\n", "\n")
        fs_fit, _ = self._hero_quote_font_sizes(int(max_w), box_h, raw)
        if mx:
            oq.setMinimumHeight(100)
            fs = min(14, max(10, fs_fit))
        else:
            oq.setMinimumHeight(72)
            fs = min(12, max(9, fs_fit))
        if self._dark:
            oq.setStyleSheet(f"font-size: {fs}pt; color: #c5ddd4; line-height: 1.45;")
        else:
            oq.setStyleSheet(f"font-size: {fs}pt; color: #143d32; line-height: 1.45;")

    def _apply_hero_quote_index(self, idx: int) -> None:
        q_text, q_author = _NYRON_MARKET_QUOTES[idx % len(_NYRON_MARKET_QUOTES)]
        self._hero_quote_text.setText(f"«{q_text}»")
        self._hero_quote_author.setText(f"— {q_author}")
        self._adjust_hero_layout()

    def _rotate_hero_quote(self) -> None:
        n = len(_NYRON_MARKET_QUOTES)
        if n <= 1:
            return
        choices = [i for i in range(n) if i != self._hero_quote_last_idx]
        self._hero_quote_last_idx = random.choice(choices)
        self._apply_hero_quote_index(self._hero_quote_last_idx)

    def _toggle_theme(self):
        self._dark = not self._dark
        self._apply_stylesheet()
        self._refresh_all_action_icons()
        if getattr(self, "_glossary_browser", None) is not None:
            apply_glossary_browser_style(self._glossary_browser, self._dark)
        ed = getattr(self, "_embedded_detail", None)
        if ed is not None:
            ed.apply_theme(self._dark)
        # Theme switch must also refresh already-rendered table items.
        # Otherwise, items created in dark theme keep dark backgrounds/foregrounds in light theme.
        try:
            if getattr(self, "_results", None):
                self._fill_main_table()
                self._fill_opportunity_tables()
                self._fill_movers_tables()
                self._refresh_favorites_table()
        except Exception:
            logger.debug("Tema geçişinde tablo yenileme başarısız", exc_info=True)
        self._sync_responsive_layout()

    def _make_brand_logo_label(self) -> QLabel | None:
        path = branding.resolve_brand_logo_path()
        if path is None:
            return None
        pm = branding.scaled_brand_pixmap(path)
        if pm is None:
            return None
        lbl = QLabel()
        lbl.setObjectName("brandLogo")
        lbl.setPixmap(pm)
        lbl.setToolTip(_APP_NAME)
        return lbl

    def _on_results_tab_changed(self, index: int) -> None:
        if self._tabs.widget(index) is self._tab_opp:
            self._refresh_opp_hero_quote()

    def _refresh_opp_hero_quote(self) -> None:
        if not hasattr(self, "_opp_hero_quote"):
            return
        q, author = random.choice(_NYRON_MARKET_QUOTES)
        self._opp_hero_quote.setText(f"«{q}»\n\n— {author}")
        self._adjust_opp_hero_layout()

    @staticmethod
    def _clip_cell_text(s: str, max_len: int = 72) -> str:
        s = (s or "").strip()
        if len(s) <= max_len:
            return s
        return s[: max_len - 1] + "…"

    def _build_tab_all(self):
        self._tab_all = QWidget()
        lay = QVBoxLayout(self._tab_all)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(6)

        filter_sidebar = QFrame()
        filter_sidebar.setObjectName("filterSidebar")
        # Filtre menüsü uzun etiketler içeriyor; dar ekranda taşmayı azaltmak için minimumu yükselt.
        filter_sidebar.setMinimumWidth(280)
        filter_sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sb_lay = QVBoxLayout(filter_sidebar)
        sb_lay.setContentsMargins(0, 0, 8, 0)
        sb_lay.setSpacing(0)

        sb_title = QLabel("Filtreler")
        sb_title.setObjectName("filterSidebarTitle")
        sb_lay.addWidget(sb_title)

        scroll = QScrollArea()
        scroll.setObjectName("filterSidebarScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inner = QWidget()
        inner.setObjectName("filterSidebarInner")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(8, 8, 8, 8)
        inner_lay.setSpacing(6)

        gb_search = QGroupBox("Arama")
        gb_search.setObjectName("filterSidebarGroup")
        sv = QVBoxLayout(gb_search)
        sv.setSpacing(6)
        self._f_text_search = QLineEdit()
        self._f_text_search.setPlaceholderText("Hisse, sektör, özet…")
        self._f_text_search.setToolTip("Enter veya Ara; yan paneldeki tüm seçimler birlikte VE ile uygulanır.")
        self._f_text_search.returnPressed.connect(self._apply_text_search_slot)
        self._btn_f_search = QPushButton("Ara")
        self._btn_f_search.setObjectName("accent")
        self._btn_f_search.setToolTip("Metin + filtreleri uygula.")
        self._btn_f_search.clicked.connect(self._apply_text_search_slot)
        sv.addWidget(self._f_text_search)
        sv.addWidget(self._btn_f_search)
        inner_lay.addWidget(gb_search)

        gb_cat = QGroupBox("Sınıf")
        gb_cat.setObjectName("filterSidebarGroup")
        form_cat = QFormLayout(gb_cat)
        form_cat.setSpacing(6)
        form_cat.setContentsMargins(8, 10, 8, 8)
        form_cat.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_cat.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._f_signal = QComboBox()
        for _lbl, _code in (
            ("Tümü", "Tümü"),
            ("Al", "BUY"),
            ("Tut", "WAIT"),
            ("Sat", "SELL"),
        ):
            self._f_signal.addItem(_lbl, _code)
        self._f_sector = QComboBox()
        self._f_sector.addItem("Tümü")
        self._f_trend = QComboBox()
        self._f_trend.addItem("Tümü")
        self._f_trend.setToolTip("SMA yapısına göre trend etiketi.")
        for c in (self._f_signal, self._f_sector, self._f_trend):
            c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_cat.addRow("Sinyal", self._f_signal)
        form_cat.addRow("Sektör", self._f_sector)
        form_cat.addRow("Trend", self._f_trend)
        inner_lay.addWidget(gb_cat)

        gb_num = QGroupBox("Aralık")
        gb_num.setObjectName("filterSidebarGroup")
        form_num = QFormLayout(gb_num)
        form_num.setSpacing(6)
        form_num.setContentsMargins(8, 10, 8, 8)
        form_num.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_num.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        def _pair_row(wmin: QLineEdit, wmax: QLineEdit) -> QWidget:
            wmin.setPlaceholderText("min")
            wmax.setPlaceholderText("max")
            for w in (wmin, wmax):
                w.setMinimumWidth(44)
                w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            r = QHBoxLayout()
            r.setSpacing(4)
            r.setContentsMargins(0, 0, 0, 0)
            r.addWidget(wmin, 1)
            r.addWidget(QLabel("–"))
            r.addWidget(wmax, 1)
            o = QWidget()
            o.setLayout(r)
            return o

        self._f_rsi_min = QLineEdit()
        self._f_rsi_max = QLineEdit()
        form_num.addRow("RSI", _pair_row(self._f_rsi_min, self._f_rsi_max))
        self._f_sc_min = QLineEdit()
        self._f_sc_max = QLineEdit()
        form_num.addRow("Skor", _pair_row(self._f_sc_min, self._f_sc_max))
        self._f_pct1d_min = QLineEdit()
        self._f_pct1d_max = QLineEdit()
        form_num.addRow("Gün %", _pair_row(self._f_pct1d_min, self._f_pct1d_max))
        inner_lay.addWidget(gb_num)

        atr_hi = SCREEN.get("filter_atr_high_pct", 2.5)
        atr_lo = SCREEN.get("filter_atr_low_pct", 1.5)
        sc_hi = int(SCREEN.get("filter_score_strong", 70))
        sc_lo = int(SCREEN.get("filter_score_weak", 40))

        gb_combo = QGroupBox("Kombinasyonlar")
        gb_combo.setObjectName("filterSidebarGroup")
        combo_lay = QVBoxLayout(gb_combo)
        combo_lay.setSpacing(4)
        combo_lay.setContentsMargins(8, 10, 8, 8)
        combo_hint = QLabel("İşaretlenenlerin hepsi aynı anda sağlanmalı (VE).")
        combo_hint.setObjectName("filterSidebarHint")
        combo_hint.setWordWrap(True)
        combo_lay.addWidget(combo_hint)

        self._f_anom = QCheckBox("Uyumsuzluk uyarısı")
        self._f_vol = QCheckBox("Hacim sıçraması (>1,5×)")
        self._f_liq = QCheckBox("Likidite (hacim ≥ 30g ort.)")
        self._f_liq.setToolTip(f"Son gün hacmi ≥ {SCREEN.get('min_vol_ratio_liquidity', 1.0)} × 30g ort.")
        self._f_rs_pos = QCheckBox("Endeks üstü (RS↔100 > 0)")
        self._f_rs_pos.setToolTip("Yaklaşık 20 işlem günü getirisi, referans endekse göre pozitif.")
        self._f_p20_up = QCheckBox("20g yükselişte")
        self._f_p20_dn = QCheckBox("20g düşüşte")
        self._f_p1_up = QCheckBox("Bugün pozitif %")
        self._f_p1_dn = QCheckBox("Bugün negatif %")
        self._f_atr_hi = QCheckBox(f"Yüksek oynaklık (ATR % ≥ {atr_hi})")
        self._f_atr_lo = QCheckBox(f"Düşük oynaklık (ATR % ≤ {atr_lo})")
        self._f_sc_hi = QCheckBox(f"Güçlü skor (≥ {sc_hi})")
        self._f_sc_lo = QCheckBox(f"Zayıf skor (≤ {sc_lo})")
        for cb in (
            self._f_anom,
            self._f_vol,
            self._f_liq,
            self._f_rs_pos,
            self._f_p20_up,
            self._f_p20_dn,
            self._f_p1_up,
            self._f_p1_dn,
            self._f_atr_hi,
            self._f_atr_lo,
            self._f_sc_hi,
            self._f_sc_lo,
        ):
            combo_lay.addWidget(cb)
        inner_lay.addWidget(gb_combo)

        btn_apply = QPushButton("Uygula")
        btn_apply.setObjectName("accent")
        btn_apply.setToolTip("Tüm filtreleri tabloya yansıt.")
        btn_apply.clicked.connect(self._apply_filters_slot)
        btn_reset = QPushButton("Sıfırla")
        btn_reset.setToolTip("Arama, sınıf, aralık ve kombinasyonları temizle.")
        btn_reset.clicked.connect(self._reset_filters_slot)
        inner_lay.addWidget(btn_apply)
        inner_lay.addWidget(btn_reset)
        inner_lay.addStretch()

        scroll.setWidget(inner)
        sb_lay.addWidget(scroll, 1)

        table_shell = QFrame()
        table_shell.setObjectName("resultsTableShell")
        ts_lay = QVBoxLayout(table_shell)
        ts_lay.setContentsMargins(10, 10, 10, 10)
        ts_lay.setSpacing(8)
        self._lbl_results_count = QLabel("Tarama sonrası satırlar burada listelenir.")
        self._lbl_results_count.setObjectName("resultsCountLabel")
        self._lbl_results_count.setWordWrap(True)
        ts_lay.addWidget(self._lbl_results_count)

        self._table = QTableWidget(0, 14)
        self._table.setObjectName("resultsTable")
        _main_hdr = [
            "Hisse",
            "Sektör",
            "Fiyat",
            "Gün %",
            "20g %",
            "RS↔100",
            "Hacim×",
            "ATR %",
            "Trend",
            "RSI",
            "Skor",
            "Sinyal",
            "Özet",
            "Uyumsuzluk",
        ]
        self._table.setHorizontalHeaderLabels(_main_hdr)
        self._set_horizontal_header_tooltips(
            self._table,
            [
                "Borsa İstanbul sembolü (.IS).",
                "Sektör sınıflaması (veri kaynağına göre).",
                "Son işlem günü kapanış fiyatı (₺).",
                "Bir önceki işlem günü kapanışına göre günlük yüzde değişim.",
                "Son yaklaşık 20 işlem gününde toplam yüzde getiri.",
                f"BIST 100 ({BENCHMARK.get('ticker', 'XU100.IS')}) endeksine göre ~20 işlem günü göreli güç farkı (yüzde puan).",
                "Son gün işlem hacminin son 30 günlük ortalama hacme bölümü (×).",
                "ATR / fiyat — günlük volatilite yaklaşımı (%).",
                "SMA yapısı ve kısa momentumdan türetilen özet trend etiketi.",
                "14 periyot RSI: aşırı alım/satım bölgeleri için yaygın momentum göstergesi.",
                "0–100 arası birleşik teknik skor (model ağırlıkları config’te).",
                "Model çıktısı: Al / Tut / Sat (skora göre Güçlü al veya Güçlü sat) — tek başına işlem emri değildir.",
                "Kısa teknik özet satırı (getiri, göreli güç, trend vb.).",
                "Uyumsuzluk / anomali etiketi; sarı satırlarda teknik alarm olabilir.",
            ],
        )
        hdr = self._table.horizontalHeader()
        hdr.setMinimumSectionSize(48)
        hdr.setHighlightSections(False)
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 82)
        for i in range(1, 12):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(12, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(13, QHeaderView.ResizeMode.Interactive)
        self._table.setAlternatingRowColors(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setToolTip("Çift tıklayarak grafik, indikatör, uyumsuzluk ve özet sekmelerini açın.")
        self._table.cellDoubleClicked.connect(self._on_main_table_dblclick)
        self._table.verticalHeader().setDefaultSectionSize(30)
        ts_lay.addWidget(self._table, 1)

        split.addWidget(filter_sidebar)
        split.addWidget(table_shell)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([340, 980])
        lay.addWidget(split, 1)

    def _configure_full_height_table(self, tbl: QTableWidget, stretch_col: int) -> None:
        hdr = tbl.horizontalHeader()
        hdr.setMinimumSectionSize(52)
        hdr.setHighlightSections(False)
        n = tbl.columnCount()
        for c in range(n):
            if c == stretch_col:
                hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)
            else:
                hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Interactive)
        tbl.setAlternatingRowColors(True)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(34)
        tbl.setShowGrid(True)

    @staticmethod
    def _set_horizontal_header_tooltips(tbl: QTableWidget, tips: list[str]) -> None:
        for i in range(tbl.columnCount()):
            hi = tbl.horizontalHeaderItem(i)
            if hi is None:
                continue
            if i < len(tips) and tips[i]:
                hi.setToolTip(tips[i])

    def _build_tab_opportunities(self):
        self._tab_opp = QWidget()
        outer = QVBoxLayout(self._tab_opp)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        shell = QFrame()
        shell.setObjectName("oppPremiumShell")
        lay = QVBoxLayout(shell)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("oppPremiumHero")
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(20, 18, 20, 18)
        hl.setSpacing(8)
        badge = QLabel("ÖNE ÇIKANLAR")
        badge.setObjectName("oppPremiumBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ht = QLabel("Fırsat merkezi")
        ht.setObjectName("oppPremiumHeroTitle")
        ht.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._opp_quote_row = QWidget()
        self._opp_quote_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        oqr = QHBoxLayout(self._opp_quote_row)
        oqr.setContentsMargins(0, 0, 0, 0)
        oqr.setSpacing(0)
        oqr.addStretch(1)
        self._opp_hero_quote = QLabel()
        self._opp_hero_quote.setObjectName("oppPremiumHeroSub")
        self._opp_hero_quote.setWordWrap(True)
        self._opp_hero_quote.setMinimumHeight(52)
        self._opp_hero_quote.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self._opp_hero_quote.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        oqr.addWidget(self._opp_hero_quote, 0, Qt.AlignmentFlag.AlignVCenter)
        oqr.addStretch(1)
        hl.addWidget(badge, 0, Qt.AlignmentFlag.AlignHCenter)
        hl.addWidget(ht, 0, Qt.AlignmentFlag.AlignHCenter)
        hl.addStretch(1)
        hl.addWidget(self._opp_quote_row, 0, Qt.AlignmentFlag.AlignHCenter)
        hl.addStretch(1)
        lay.addWidget(hero)

        sub = QTabWidget()
        sub.setObjectName("oppPremiumTabs")
        sub.setDocumentMode(True)

        w_buy = QWidget()
        vb = QVBoxLayout(w_buy)
        vb.setContentsMargins(10, 10, 10, 10)
        buy_row = QHBoxLayout()
        buy_row.setSpacing(10)

        tbl_wrap = QWidget()
        tw_lay = QVBoxLayout(tbl_wrap)
        tw_lay.setContentsMargins(0, 0, 0, 0)
        self._tbl_buy = QTableWidget(0, 8)
        self._tbl_buy.setHorizontalHeaderLabels(
            ["Hisse", "Skor", "RSI", "Sinyal", "Fiyat", "20g %", "RS↔100", "Özet"]
        )
        self._set_horizontal_header_tooltips(
            self._tbl_buy,
            [
                "Hisse sembolü.",
                "0–100 teknik skor; model alımda eşik üzeri gerekir.",
                "14 periyot RSI; listede kalmak için üst sınırın altında olmalı (aşırı alım filtresi).",
                "Model sinyali; bu sekmede çoğunlukla «Al».",
                "Son işlem günü kapanış (₺).",
                "Son ~20 işlem günü yüzde getiri.",
                f"BIST 100’e göre ~20 işlem günü göreli güç (pp), {BENCHMARK.get('ticker', 'XU100.IS')}.",
                "Kısa teknik özet; ayrıntılı gerekçe sağdaki “Neden bu hisse?” panelinde.",
            ],
        )
        self._configure_full_height_table(self._tbl_buy, 7)
        self._tbl_buy.setObjectName("oppDataTable")
        self._tbl_buy.setColumnWidth(0, 100)
        self._tbl_buy.setColumnWidth(1, 56)
        self._tbl_buy.setColumnWidth(2, 56)
        self._tbl_buy.setColumnWidth(3, 64)
        self._tbl_buy.setColumnWidth(4, 88)
        self._tbl_buy.setColumnWidth(5, 72)
        self._tbl_buy.setColumnWidth(6, 72)
        self._tbl_buy.cellDoubleClicked.connect(lambda *_: self._open_detail_from_table(self._tbl_buy, 0))
        tw_lay.addWidget(self._tbl_buy, 1)
        buy_row.addWidget(tbl_wrap, 1)

        self._why_fr_buy = QFrame()
        self._why_fr_buy.setObjectName("oppWhyPanel")
        self._why_fr_buy.setMinimumWidth(220)
        self._why_fr_buy.setMaximumWidth(300)
        why_fr = self._why_fr_buy
        wfl = QVBoxLayout(why_fr)
        wfl.setContentsMargins(10, 8, 10, 8)
        wfl.setSpacing(6)
        wt = QLabel("Neden bu hisse?")
        wt.setObjectName("sectionTitle")
        self._lbl_buy_why = QLabel(
            "Soldan bir satır seçin; model alım kriterlerine göre özet gerekçe burada görünür."
        )
        self._lbl_buy_why.setObjectName("sectionSub")
        self._lbl_buy_why.setWordWrap(True)
        self._lbl_buy_why.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._lbl_buy_why.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        why_scroll = QScrollArea()
        why_scroll.setWidgetResizable(True)
        why_scroll.setFrameShape(QFrame.Shape.NoFrame)
        why_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        why_scroll.setMinimumWidth(200)
        why_inner = QWidget()
        why_il = QVBoxLayout(why_inner)
        why_il.setContentsMargins(0, 0, 0, 0)
        why_il.setSpacing(6)
        why_il.addWidget(self._lbl_buy_why)
        why_scroll.setWidget(why_inner)
        wfl.addWidget(wt)
        wfl.addWidget(why_scroll, 1)
        buy_row.addWidget(why_fr, 0)
        vb.addLayout(buy_row, 1)

        self._tbl_buy.itemSelectionChanged.connect(self._on_buy_table_selection_changed)

        sub.addTab(w_buy, "Model alım")

        w_an = QWidget()
        va = QVBoxLayout(w_an)
        va.setContentsMargins(10, 10, 10, 10)
        self._tbl_anom = QTableWidget(0, 5)
        self._tbl_anom.setHorizontalHeaderLabels(["Hisse", "Skor", "Sinyal", "Yön", "Tetikleyiciler"])
        self._set_horizontal_header_tooltips(
            self._tbl_anom,
            [
                "Hisse sembolü.",
                "Teknik skor.",
                "Model sinyali (Al / Tut / Sat).",
                "Skora göre baskın yön özeti (alım / satış tarafı).",
                "Uyumsuzluk modelinin işaretlediği tetikleyiciler (tam metin için üzerine gelin).",
            ],
        )
        self._configure_full_height_table(self._tbl_anom, 4)
        self._tbl_anom.setObjectName("oppDataTable")
        self._tbl_anom.setColumnWidth(0, 100)
        self._tbl_anom.setColumnWidth(1, 56)
        self._tbl_anom.setColumnWidth(2, 64)
        self._tbl_anom.setColumnWidth(3, 120)
        self._tbl_anom.cellDoubleClicked.connect(lambda *_: self._open_detail_from_table(self._tbl_anom, 0))
        va.addWidget(self._tbl_anom, 1)
        sub.addTab(w_an, "Uyumsuzluk")

        w_vol = QWidget()
        vv = QVBoxLayout(w_vol)
        vv.setContentsMargins(10, 10, 10, 10)
        self._tbl_vol = QTableWidget(0, 5)
        self._tbl_vol.setHorizontalHeaderLabels(["Hisse", "Skor", "Hacim ×", "Fiyat", "Trend"])
        self._set_horizontal_header_tooltips(
            self._tbl_vol,
            [
                "Hisse sembolü.",
                "Teknik skor.",
                "Son gün hacminin 30 günlük ortalamaya oranı.",
                "Son kapanış (₺).",
                "Özet trend etiketi.",
            ],
        )
        self._configure_full_height_table(self._tbl_vol, 4)
        self._tbl_vol.setObjectName("oppDataTable")
        self._tbl_vol.setColumnWidth(0, 100)
        self._tbl_vol.setColumnWidth(1, 56)
        self._tbl_vol.setColumnWidth(2, 72)
        self._tbl_vol.setColumnWidth(3, 88)
        self._tbl_vol.cellDoubleClicked.connect(lambda *_: self._open_detail_from_table(self._tbl_vol, 0))
        vv.addWidget(self._tbl_vol, 1)
        sub.addTab(w_vol, "Hacim")

        lay.addWidget(sub, 1)
        outer.addWidget(shell, 1)

    def _build_tab_movers(self):
        self._tab_mov = QWidget()
        outer = QVBoxLayout(self._tab_mov)
        hint = QFrame()
        hint.setObjectName("welcomeCard")
        hl = QVBoxLayout(hint)
        hl.setContentsMargins(14, 12, 14, 12)
        ht = QLabel("Günün hareketleri")
        ht.setObjectName("welcomeTitle")
        hb = QLabel(
            "Son işlem gününün bir önceki güne göre kapanış değişimine göre sıralama yapılır. "
            "Tablolar bilgi amaçlıdır; çift tık ile hisse detayına gidebilirsiniz."
        )
        hb.setObjectName("welcomeBody")
        hb.setWordWrap(True)
        hl.addWidget(ht)
        hl.addWidget(hb)
        outer.addWidget(hint)
        lay = QHBoxLayout()
        lay.setSpacing(14)
        self._tbl_up = QTableWidget(0, 6)
        self._tbl_dn = QTableWidget(0, 6)
        _mov_tips = [
            "Sıra numarası.",
            "Hisse sembolü.",
            "Son işlem günü, bir önceki güne göre kapanış değişimi (%).",
            "Son kapanış (₺).",
            "Teknik skor.",
            "Model sinyali.",
        ]
        self._tbl_up.setHorizontalHeaderLabels(["#", "Hisse", "Günlük %", "Fiyat", "Skor", "Sinyal"])
        self._set_horizontal_header_tooltips(self._tbl_up, _mov_tips)
        self._tbl_dn.setHorizontalHeaderLabels(["#", "Hisse", "Günlük %", "Fiyat", "Skor", "Sinyal"])
        self._set_horizontal_header_tooltips(self._tbl_dn, _mov_tips)
        for t in (self._tbl_up, self._tbl_dn):
            t.horizontalHeader().setMinimumSectionSize(52)
            t.horizontalHeader().setStretchLastSection(True)
            t.setAlternatingRowColors(True)
            t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            t.verticalHeader().setVisible(False)
            t.verticalHeader().setDefaultSectionSize(30)
        self._tbl_up.cellDoubleClicked.connect(lambda *_: self._open_detail_from_table(self._tbl_up, 1))
        self._tbl_dn.cellDoubleClicked.connect(lambda *_: self._open_detail_from_table(self._tbl_dn, 1))
        gu = QGroupBox("En çok yükselenler (günlük %)")
        gul = QVBoxLayout(gu)
        gu_sub = QLabel("Pozitif kapanış değişimi en yüksek olanlar.")
        gu_sub.setObjectName("sectionSub")
        gu_sub.setWordWrap(True)
        gul.addWidget(gu_sub)
        gul.addWidget(self._tbl_up)
        gd = QGroupBox("En çok düşenler (günlük %)")
        gdl = QVBoxLayout(gd)
        gd_sub = QLabel("Negatif kapanış değişimi en derin olanlar.")
        gd_sub.setObjectName("sectionSub")
        gd_sub.setWordWrap(True)
        gdl.addWidget(gd_sub)
        gdl.addWidget(self._tbl_dn)
        lay.addWidget(gu, 1)
        lay.addWidget(gd, 1)
        outer.addLayout(lay, 1)

    def _start_scan(self):
        if self._worker and self._worker.isRunning():
            return
        self._btn_run.setEnabled(False)
        self._prog.setValue(0)
        self._prog_lbl.setText("")
        self._chip_market_l.setText("Çalışıyor")
        self._log.clear()
        self._worker = AnalysisWorker(self._analyzer)
        self._worker.progress.connect(self._on_progress, Qt.ConnectionType.QueuedConnection)
        self._worker.finished_ok.connect(self._on_scan_done, Qt.ConnectionType.QueuedConnection)
        self._worker.failed.connect(self._on_scan_fail, Qt.ConnectionType.QueuedConnection)
        self._worker.start()
        self._btn_cont.hide()

    def _on_progress(self, cur: int, total: int):
        self._prog_lbl.setText(f"{cur}/{total}")
        if not total:
            return
        # Update target; actual bar moves smoothly via timer.
        self._prog_target = int(100 * cur / total)
        if not self._prog_timer.isActive():
            self._prog_timer.start()

    def _tick_progress_animation(self) -> None:
        cur = int(self._prog.value())
        tgt = int(getattr(self, "_prog_target", cur))
        if cur >= tgt:
            # Stop once caught up; also stop at 100 to save cycles.
            if cur >= 100 or cur == tgt:
                self._prog_timer.stop()
            return
        # Step size increases a bit when the gap is large.
        gap = tgt - cur
        step = 1 if gap < 8 else 2 if gap < 20 else 3
        self._prog.setValue(min(tgt, cur + step))

    def _on_scan_done(self, results):
        try:
            self._results = results or []
            self._all_data = getattr(self._analyzer, "all_data", {}) or {}
            self._results_dict = getattr(self._analyzer, "results_dict", {}) or {}
            ac.decorate_results(self._results, self._all_data)
            try:
                scores = [r.get("score") for r in self._results if isinstance(r, dict)]
                scores_num = [float(s) for s in scores if isinstance(s, (int, float))]
                missing = sum(1 for s in scores if s is None)
                if scores_num:
                    logger.info(
                        "Skor özeti: min=%.2f max=%.2f (eksik=%s/%s)",
                        min(scores_num),
                        max(scores_num),
                        missing,
                        len(scores),
                    )
                else:
                    logger.warning("Skor özeti: sayısal skor bulunamadı (eksik=%s/%s)", missing, len(scores))
            except Exception:
                logger.debug("Skor özeti loglanamadı", exc_info=True)
            self._update_sector_combo()
            n = len(self._results)
            self._chip_scan_l.setText(f"{n} hisse")
            self._chip_market_l.setText("Tamamlandı")
            b = getattr(self._analyzer, "benchmark_20d_return", None)
            if b is not None:
                self._chip_bench_l.setText(f"{b:+.2f}% (~20 iş günü)")
            else:
                self._chip_bench_l.setText("—")
            self._prog.setValue(100)
            if self._results:
                self._btn_cont.show()
            else:
                self._btn_cont.hide()
            logger.info("Tarama tamamlandı: %s hisse", n)
        except Exception as exc:
            logger.exception("Sonuç işleme")
            self._btn_cont.hide()
            QMessageBox.warning(self, "Uyarı", str(exc))
        finally:
            self._btn_run.setEnabled(True)

    def _on_scan_fail(self, msg: str):
        self._btn_run.setEnabled(True)
        self._btn_cont.hide()
        self._chip_market_l.setText("Hata")
        QMessageBox.critical(self, "Hata", msg)
        logger.error("Tarama hatası: %s", msg)

    def _update_sector_combo(self):
        self._f_sector.blockSignals(True)
        self._f_sector.clear()
        self._f_sector.addItem("Tümü")
        sectors = sorted({r.get("sector", "Bilinmiyor") for r in self._results})
        self._f_sector.addItems(sectors)
        self._f_sector.blockSignals(False)

        self._f_trend.blockSignals(True)
        prev_t = self._f_trend.currentText() if self._f_trend.count() else "Tümü"
        self._f_trend.clear()
        self._f_trend.addItem("Tümü")
        trends = sorted({r.get("trend_label", "—") for r in self._results if r.get("trend_label") not in (None, "", "—")})
        self._f_trend.addItems(trends)
        ix = self._f_trend.findText(prev_t)
        self._f_trend.setCurrentIndex(max(0, ix))
        self._f_trend.blockSignals(False)

    def _show_results_view(self):
        if not self._results:
            return
        self._stack.setCurrentIndex(1)
        self._btn_run.hide()
        self._btn_cont.hide()
        self._btn_refresh.show()
        self._btn_csv.show()
        self._apply_filters_slot()

    def _reset_scan(self):
        self._teardown_embedded_detail()
        self._results = []
        self._filtered = []
        self._all_data = {}
        self._results_dict = {}
        self._f_text_search.clear()
        self._stack.setCurrentIndex(0)
        self._btn_run.show()
        self._btn_cont.hide()
        self._btn_refresh.hide()
        self._btn_csv.hide()
        self._prog.setValue(0)
        self._prog_lbl.setText("")
        self._chip_market_l.setText("Hazır")
        self._chip_scan_l.setText("—")
        self._chip_bench_l.setText("—")
        self.setWindowTitle(_APP_NAME)

    def _reset_filters_slot(self):
        self._f_signal.setCurrentIndex(0)
        self._f_sector.setCurrentIndex(0)
        self._f_trend.setCurrentIndex(0)
        self._f_rsi_min.clear()
        self._f_rsi_max.clear()
        self._f_sc_min.clear()
        self._f_sc_max.clear()
        self._f_pct1d_min.clear()
        self._f_pct1d_max.clear()
        self._f_anom.setChecked(False)
        self._f_vol.setChecked(False)
        self._f_liq.setChecked(False)
        self._f_rs_pos.setChecked(False)
        self._f_p20_up.setChecked(False)
        self._f_p20_dn.setChecked(False)
        self._f_p1_up.setChecked(False)
        self._f_p1_dn.setChecked(False)
        self._f_atr_hi.setChecked(False)
        self._f_atr_lo.setChecked(False)
        self._f_sc_hi.setChecked(False)
        self._f_sc_lo.setChecked(False)
        self._f_text_search.clear()
        self._apply_filters_slot()

    def _apply_text_search_slot(self):
        if not self._results:
            return
        self._tabs.setCurrentWidget(self._tab_all)
        self._apply_filters_slot()
        if self._table.rowCount() > 0:
            self._table.selectRow(0)
            self._table.scrollToItem(self._table.item(0, 0))

    def _apply_filters_slot(self):
        if not self._results:
            return
        self._filtered = ac.apply_filters(
            self._results,
            ac.signal_filter_from_combo(self._f_signal.currentData()),
            self._f_sector.currentText(),
            ac.parse_filter_float(self._f_rsi_min.text()),
            ac.parse_filter_float(self._f_rsi_max.text()),
            ac.parse_filter_float(self._f_sc_min.text()),
            ac.parse_filter_float(self._f_sc_max.text()),
            self._f_anom.isChecked(),
            self._f_vol.isChecked(),
            self._f_liq.isChecked(),
            text_query=self._f_text_search.text(),
            trend_filter=self._f_trend.currentText(),
            pct1d_min=ac.parse_filter_float(self._f_pct1d_min.text()),
            pct1d_max=ac.parse_filter_float(self._f_pct1d_max.text()),
            rs_outperform=self._f_rs_pos.isChecked(),
            pct20_positive=self._f_p20_up.isChecked(),
            pct20_negative=self._f_p20_dn.isChecked(),
            pct1d_positive=self._f_p1_up.isChecked(),
            pct1d_negative=self._f_p1_dn.isChecked(),
            atr_high=self._f_atr_hi.isChecked(),
            atr_low=self._f_atr_lo.isChecked(),
            score_strong=self._f_sc_hi.isChecked(),
            score_weak=self._f_sc_lo.isChecked(),
        )
        self._fill_main_table()
        self._fill_opportunity_tables()
        self._fill_movers_tables()
        self._update_results_count_label()

    def _update_results_count_label(self):
        if not self._results:
            self._lbl_results_count.setText("Önce tarama yapın.")
            return
        n_f = len(self._filtered)
        n_t = len(self._results)
        self._lbl_results_count.setText(f"{n_f} / {n_t} hisse gösteriliyor.")

    def _export_csv_slot(self):
        if not self._filtered:
            QMessageBox.information(self, "CSV", "Önce tarama yapıp filtre uygulayın.")
            return
        suggested = ac.suggested_scan_results_csv_filename()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Tarama sonucu CSV kaydet",
            str(Path.cwd() / suggested),
            "CSV (*.csv)",
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        saved = ac.export_results_csv(self._filtered, path=path)
        if saved:
            QMessageBox.information(self, "Dışa aktarma", "Tablo seçtiğiniz konuma kaydedildi.")
        else:
            QMessageBox.warning(self, "CSV", "Dosya yazılamadı (izin veya yol).")

    def _main_table_row_background(self, r: dict) -> QColor | None:
        """Fırsat / sinyal / uyarı önceliğine göre satır zemini (daha yumuşak, göze uyumlu)."""
        if ac.is_buy_opportunity_candidate(r):
            return QColor("#0f2d24") if self._dark else QColor("#d4f5e5")
        if r.get("anomaly_color") == "yellow":
            return QColor("#3a3020") if self._dark else QColor("#fff4e0")
        sig = r.get("signal", "")
        if sig == "SELL":
            return QColor("#3a1f24") if self._dark else QColor("#fde8ef")
        if sig == "BUY":
            return QColor("#152a22") if self._dark else QColor("#dff7ea")
        if sig == "WAIT":
            return QColor("#1e2836") if self._dark else QColor("#e9eef9")
        return QColor("#141a22") if self._dark else QColor("#f6f8fc")

    @staticmethod
    def _fmt_pct_cell(v: float | None) -> str:
        if v is None:
            return "—"
        return f"{v:+.2f}%"

    @staticmethod
    def _fmt_num(v: float | None, nd: int = 2) -> str:
        if v is None:
            return "—"
        return f"{v:.{nd}f}"

    def _fill_main_table(self):
        t = self._table
        t.setUpdatesEnabled(False)
        t.blockSignals(True)
        try:
            t.setRowCount(0)
            for r in self._filtered:
                row = t.rowCount()
                t.insertRow(row)
                rsi_val = r.get("rsi")
                if isinstance(rsi_val, (int, float)) and not pd.isna(rsi_val):
                    rsi_s = f"{rsi_val:.1f}"
                else:
                    rsi_s = str(rsi_val) if rsi_val not in (None, "") else "—"
                vals = [
                    r["symbol"],
                    r.get("sector", "—"),
                    f"{r['price']:.2f} ₺",
                    self._fmt_pct_cell(r.get("pct_1d")),
                    self._fmt_pct_cell(r.get("pct_20d")),
                    (f"{r.get('rs_20d'):+.2f}" if r.get("rs_20d") is not None else "—"),
                    self._fmt_num(r.get("vol_ratio"), 2) if r.get("vol_ratio") is not None else "—",
                    self._fmt_num(r.get("atr_pct"), 2) if r.get("atr_pct") is not None else "—",
                    r.get("trend_label", "—"),
                    rsi_s,
                    f"{r.get('score', 0):.1f}",
                    ac.format_signal_tr(r.get("signal"), r.get("score")),
                    r.get("thesis", "—"),
                    r.get("anomaly", ""),
                ]
                bg = self._main_table_row_background(r)
                center = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(str(v))
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    it.setTextAlignment(center)
                    it.setBackground(bg)
                    t.setItem(row, c, it)
        finally:
            t.blockSignals(False)
            t.setUpdatesEnabled(True)

    def _on_buy_table_selection_changed(self) -> None:
        sm = self._tbl_buy.selectionModel()
        if sm is None:
            return
        idxs = sm.selectedRows()
        if not idxs:
            self._lbl_buy_why.setText(
                "Soldan bir satır seçin; model alım kriterlerine göre özet gerekçe burada görünür."
            )
            return
        r = idxs[0].row()
        it = self._tbl_buy.item(r, 0)
        if it is None:
            return
        sym = it.text().strip()
        data = self._buy_rows_by_symbol.get(sym)
        if not data:
            self._lbl_buy_why.setText("Bu satır için tarama verisi yok.")
            return
        self._lbl_buy_why.setText(build_opportunity_why_for_user(data))

    def _fill_opportunity_tables(self):
        self._tbl_buy.setUpdatesEnabled(False)
        self._tbl_anom.setUpdatesEnabled(False)
        self._tbl_vol.setUpdatesEnabled(False)
        self._tbl_buy.blockSignals(True)
        self._tbl_anom.blockSignals(True)
        self._tbl_vol.blockSignals(True)
        try:
            buy_list = [r for r in self._results if ac.is_buy_opportunity_candidate(r)]
            buy_list.sort(key=lambda x: x["score"], reverse=True)
            shown_buy = buy_list[:30]
            try:
                if shown_buy:
                    top = [(x.get("symbol"), float(x.get("score") or 0)) for x in shown_buy[:3]]
                    logger.info("Fırsatlar (model alım) örnek skorlar: %s", top)
                else:
                    logger.info("Fırsatlar (model alım): liste boş")
            except Exception:
                logger.debug("Fırsat skor logu üretilemedi", exc_info=True)
            self._buy_rows_by_symbol = {r["symbol"]: r for r in shown_buy}
            self._tbl_buy.setRowCount(0)
            for r in shown_buy:
                row = self._tbl_buy.rowCount()
                self._tbl_buy.insertRow(row)
                rsi = r.get("rsi")
                rs = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else str(rsi)
                p20 = r.get("pct_20d")
                p20s = f"{p20:+.2f}%" if p20 is not None else "—"
                rsv = r.get("rs_20d")
                rss = f"{rsv:+.2f}" if rsv is not None else "—"
                rationale = build_opportunity_rationale(r)
                thesis = (r.get("thesis") or "").strip()
                if thesis:
                    summary_src = thesis
                else:
                    summary_src = build_thesis_line(
                        {
                            "rs_20d": r.get("rs_20d"),
                            "trend_label": r.get("trend_label"),
                            "vol_ratio": r.get("vol_ratio"),
                            "atr_pct": r.get("atr_pct"),
                        },
                        r.get("signal"),
                        float(r.get("score") or 0),
                    )
                    if summary_src in ("", "—"):
                        summary_src = rationale
                summary_show = self._clip_cell_text(summary_src, 96)
                row_vals = [
                    r["symbol"],
                    f"{r['score']:.1f}",
                    rs,
                    ac.format_signal_tr(r.get("signal"), r.get("score")),
                    f"{r['price']:.2f}",
                    p20s,
                    rss,
                    summary_show,
                ]
                ce = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                for c, v in enumerate(row_vals):
                    it = QTableWidgetItem(str(v))
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    it.setTextAlignment(ce)
                    if c == 7:
                        why_txt = build_opportunity_why_for_user(r)
                        it.setToolTip(f"{summary_src}\n\n— Satır özeti —\n{rationale}\n\n— Neden bu hisse? —\n{why_txt}")
                    self._tbl_buy.setItem(row, c, it)

            if self._tbl_buy.rowCount() > 0:
                self._tbl_buy.selectRow(0)
            else:
                self._lbl_buy_why.setText(
                    "Şu an model alım kriterlerini sağlayan hisse yok. «Tüm sonuçlar» sekmesinden filtreleri deneyin."
                )

            anom = [r for r in self._filtered if r.get("anomaly_color") == "yellow"]
            anom.sort(key=lambda x: x["score"], reverse=True)
            self._tbl_anom.setRowCount(0)
            for r in anom[:40]:
                row = self._tbl_anom.rowCount()
                self._tbl_anom.insertRow(row)
                sk = r["score"]
                yon = "Alım tarafı" if sk >= 50 else "Satış tarafı"
                trig = (r.get("anomaly_reason") or "—").strip()
                trig_show = self._clip_cell_text(trig, 100)
                row_vals = [
                    r["symbol"],
                    f"{sk:.1f}",
                    ac.format_signal_tr(r.get("signal"), r.get("score")),
                    yon,
                    trig_show,
                ]
                ce = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                for c, v in enumerate(row_vals):
                    it = QTableWidgetItem(str(v))
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    it.setTextAlignment(ce)
                    if c == 4:
                        it.setToolTip(trig)
                    self._tbl_anom.setItem(row, c, it)

            spikes = ac.volume_spike_entries(self._filtered, self._all_data)
            self._tbl_vol.setRowCount(0)
            for r, ratio in spikes[:40]:
                row = self._tbl_vol.rowCount()
                self._tbl_vol.insertRow(row)
                row_vals = [
                    r["symbol"],
                    f"{r['score']:.1f}",
                    f"{ratio:.2f}×",
                    f"{r['price']:.2f}",
                    r.get("trend_label", "—"),
                ]
                ce = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                for c, v in enumerate(row_vals):
                    it = QTableWidgetItem(str(v))
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    it.setTextAlignment(ce)
                    self._tbl_vol.setItem(row, c, it)
        finally:
            for _t in (self._tbl_buy, self._tbl_anom, self._tbl_vol):
                _t.blockSignals(False)
                _t.setUpdatesEnabled(True)

    def _fill_movers_tables(self):
        self._tbl_up.setUpdatesEnabled(False)
        self._tbl_dn.setUpdatesEnabled(False)
        self._tbl_up.blockSignals(True)
        self._tbl_dn.blockSignals(True)
        try:
            rows = []
            for r in self._results:
                sym = r["symbol"]
                tf = ac.resolve_ticker_full(sym)
                p = ac.daily_pct_change(tf, self._all_data)
                if p is not None:
                    rows.append((r, p))
            up = sorted(rows, key=lambda x: x[1], reverse=True)[:25]
            dn = sorted(rows, key=lambda x: x[1])[:25]

            def fill(tbl, data, up_mode: bool):
                tbl.setRowCount(0)
                for i, (r, pct) in enumerate(data, 1):
                    row = tbl.rowCount()
                    tbl.insertRow(row)
                    vals = [
                        str(i),
                        r["symbol"],
                        f"{pct:+.2f}%",
                        f"{r['price']}",
                        f"{r['score']:.0f}",
                        ac.format_signal_tr(r.get("signal"), r.get("score")),
                    ]
                    bg = QColor("#13261c") if (up_mode and self._dark) else (QColor("#2c1818") if self._dark else None)
                    if not self._dark:
                        bg = QColor("#dff5e8") if up_mode else QColor("#fdecef")
                    for c, v in enumerate(vals):
                        it = QTableWidgetItem(v)
                        it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if bg:
                            it.setBackground(bg)
                        tbl.setItem(row, c, it)

            fill(self._tbl_up, up, True)
            fill(self._tbl_dn, dn, False)
        finally:
            for _t in (self._tbl_up, self._tbl_dn):
                _t.blockSignals(False)
                _t.setUpdatesEnabled(True)

    def _build_tab_favorites(self) -> None:
        self._tab_fav = QWidget()
        outer = QVBoxLayout(self._tab_fav)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        hint = QFrame()
        hint.setObjectName("welcomeCard")
        hl = QVBoxLayout(hint)
        hl.setContentsMargins(14, 12, 14, 12)
        ht = QLabel("Favoriler")
        ht.setObjectName("welcomeTitle")
        hb = QLabel(
            "Detay ekranının sağ üst köşesindeki yıldız ile favorilere ekleyip çıkarabilirsiniz. "
            "Bu liste `data/favorites.json` içinde saklanır."
        )
        hb.setObjectName("welcomeBody")
        hb.setWordWrap(True)
        hl.addWidget(ht)
        hl.addWidget(hb)
        outer.addWidget(hint)

        actions = QHBoxLayout()
        self._btn_fav_remove = QPushButton("Seçileni kaldır")
        self._btn_fav_remove.setToolTip("Seçili sembolü favorilerden çıkarır.")
        self._btn_fav_remove.clicked.connect(self._remove_selected_favorite)
        actions.addWidget(self._btn_fav_remove)
        actions.addStretch(1)
        outer.addLayout(actions)

        self._tbl_fav = QTableWidget(0, 5)
        self._tbl_fav.setObjectName("oppDataTable")
        self._tbl_fav.setHorizontalHeaderLabels(["Hisse", "Sektör", "Skor", "Sinyal", "Fiyat"])
        self._configure_full_height_table(self._tbl_fav, 1)
        self._tbl_fav.setColumnWidth(0, 100)
        self._tbl_fav.setColumnWidth(2, 70)
        self._tbl_fav.setColumnWidth(3, 90)
        self._tbl_fav.setColumnWidth(4, 90)
        self._tbl_fav.cellDoubleClicked.connect(lambda *_: self._open_detail_from_table(self._tbl_fav, 0))
        outer.addWidget(self._tbl_fav, 1)

        self._refresh_favorites_table()

    def _refresh_favorites_table(self) -> None:
        if not hasattr(self, "_tbl_fav") or self._tbl_fav is None:
            return
        t = self._tbl_fav
        t.setUpdatesEnabled(False)
        t.blockSignals(True)
        try:
            favs = sorted(self._favorites)
            t.setRowCount(0)
            if not favs:
                return

            # Map current scan results for quick lookup.
            by_clean: dict[str, dict] = {}
            for r in (self._results or []):
                sym = str(r.get("symbol", "")).strip()
                clean = sym.replace(".IS", "").upper()
                if clean:
                    by_clean[clean] = r

            for clean in favs:
                r = by_clean.get(clean)
                sym_show = clean
                sector = (r.get("sector") if r else None) or "—"
                score = f"{float(r.get('score', 0)):.1f}" if r else "—"
                sig = ac.format_signal_tr(r.get("signal"), r.get("score")) if r else "—"
                price = f"{float(r.get('price', 0)):.2f} ₺" if r and r.get("price") is not None else "—"

                row = t.rowCount()
                t.insertRow(row)
                vals = [sym_show, str(sector), str(score), str(sig), str(price)]
                ce = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(str(v))
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    it.setTextAlignment(ce)
                    t.setItem(row, c, it)
        finally:
            t.blockSignals(False)
            t.setUpdatesEnabled(True)

    def _remove_selected_favorite(self) -> None:
        tbl = getattr(self, "_tbl_fav", None)
        if tbl is None:
            return
        r = tbl.currentRow()
        if r < 0:
            return
        it = tbl.item(r, 0)
        if it is None:
            return
        clean = it.text().strip().upper().replace(".IS", "")
        if not clean:
            return
        self._fav_store.set_favorite(clean, False)
        if clean in self._favorites:
            self._favorites.remove(clean)
        self._refresh_favorites_table()

    def _on_detail_favorite_changed(self, ticker_clean: str, is_fav: bool) -> None:
        clean = (ticker_clean or "").strip().upper().replace(".IS", "")
        if not clean:
            return
        if is_fav:
            self._favorites.add(clean)
        else:
            self._favorites.discard(clean)
        self._refresh_favorites_table()

    def _on_main_table_dblclick(self, row, _col):
        sym = self._table.item(row, 0)
        if sym:
            self._open_detail(sym.text())

    def _open_detail_from_table(self, tbl: QTableWidget, col_sym: int):
        r = tbl.currentRow()
        if r < 0:
            return
        it = tbl.item(r, col_sym)
        if it:
            self._open_detail(it.text())

    def closeEvent(self, event):
        self._teardown_embedded_detail()
        t = getattr(self, "_hero_quote_timer", None)
        if t is not None:
            t.stop()
        w = self._worker
        if w is not None and w.isRunning():
            try:
                w.progress.disconnect(self._on_progress)
                w.finished_ok.disconnect(self._on_scan_done)
                w.failed.disconnect(self._on_scan_fail)
            except TypeError:
                pass
            if not w.wait(300_000):
                logger.warning("Kapanış: iş parçacığı 300s içinde bitmedi")
            self._worker = None
        event.accept()

    def _open_detail(self, symbol: str):
        from qt_app.detail_dialog import DetailView

        tf = ac.resolve_ticker_full(symbol.strip())
        df = self._all_data.get(tf)
        if df is None or df.empty:
            QMessageBox.information(self, "Veri yok", f"{tf} için veri bulunamadı.")
            return
        try:
            self._teardown_embedded_detail()
            self._embedded_detail = DetailView(self._detail_holder, tf, df, self._results_dict, self._dark)
            self._embedded_detail.back_requested.connect(self._close_detail_embedded)
            self._embedded_detail.theme_toggle_requested.connect(self._toggle_theme)
            if hasattr(self._embedded_detail, "favorite_changed"):
                self._embedded_detail.favorite_changed.connect(self._on_detail_favorite_changed)
            self._detail_holder_lay.addWidget(self._embedded_detail)
            self._stack.setCurrentIndex(2)
            self.setWindowTitle(f"{_APP_NAME} — {tf} — detay")
        except Exception as exc:
            self._stack.setCurrentIndex(1)
            logger.exception("Detay ekranı")
            QMessageBox.warning(self, "Detay", str(exc))


def run_app():
    def _excepthook(exc_type, exc, tb):
        logging.getLogger("app.crash").critical("Yakalanmamış istisna", exc_info=(exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook

    app = QApplication(sys.argv)
    app.setApplicationName(_APP_NAME)
    app.setOrganizationName(_APP_NAME)
    if sys.platform == "win32":
        try:
            import ctypes

            _aid = f"{_APP_NAME.replace(' ', '')}.Desktop.1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_aid)
        except Exception:
            pass
    _ico = branding.try_load_brand_icon()
    if _ico is not None:
        app.setWindowIcon(_ico)
    from qt_app.legal_disclaimer import show_legal_disclaimer

    if not show_legal_disclaimer():
        sys.exit(0)
    w = MainWindow()
    if _ico is not None:
        w.setWindowIcon(_ico)
    w.show()
    sys.exit(app.exec())
