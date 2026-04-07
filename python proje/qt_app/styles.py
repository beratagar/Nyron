# -*- coding: utf-8 -*-
"""Uygulama geneli QSS (dark / light)."""


def stylesheet_dark() -> str:
    return """
    QWidget { font-family: "Segoe UI", "Tahoma", sans-serif; font-size: 13px; color: #e8eef4; }
    QMainWindow, QWidget#centralRoot, QDialog { background-color: #0a0e14; }
    QDialog QLabel { color: #e8eef4; }
    QMenuBar { background-color: #121922; border-bottom: 1px solid #2d3d52; spacing: 4px; }
    QMenuBar::item { padding: 8px 14px; background: transparent; }
    QMenuBar::item:selected { background-color: #1c2633; }
    QMenu { background-color: #121922; border: 1px solid #2d3d52; }
    QMenu::item:selected { background-color: #243548; }
    QGroupBox {
        border: 1px solid #2d3d52; border-radius: 10px; margin-top: 12px;
        padding: 14px 12px 12px 12px; background-color: #121922; font-weight: 600;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #8a9caf; }
    QPushButton {
        background-color: #1c2633; color: #e8eef4; border: 1px solid #2d3d52;
        border-radius: 8px; padding: 10px 18px; min-height: 20px;
    }
    QPushButton:hover { background-color: #243040; border-color: #3dd9a8; }
    QPushButton:pressed { background-color: #171f2a; }
    QPushButton#primary { background-color: #3dd9a8; color: #0a0e14; border: none; font-weight: 600; }
    QPushButton#primary:hover { background-color: #52e0b5; }
    QPushButton#accent { background-color: #6b9fff; color: #0a0e14; border: none; font-weight: 600; }
    QPushButton#accent:hover { background-color: #85b0ff; }
    QLineEdit, QComboBox {
        background-color: #0e141c; border: 1px solid #2d3d52; border-radius: 8px;
        padding: 8px 10px; min-height: 22px; selection-background-color: #3dd9a8;
        selection-color: #0a0e14;
    }
    QComboBox::drop-down { border: none; width: 28px; }
    QComboBox QAbstractItemView {
        background-color: #121922; border: 1px solid #2d3d52; selection-background-color: #243548;
    }
    QProgressBar {
        border: 1px solid #2d3d52; border-radius: 8px; text-align: center;
        background-color: #0e141c; min-height: 18px; color: #e8eef4;
    }
    QProgressBar::chunk { background-color: #3dd9a8; border-radius: 6px; }
    QTabWidget::pane { border: 1px solid #2d3d52; border-radius: 10px; top: 0px; background: #121922; }
    QTabBar::tab {
        background: #171f2a; color: #8a9caf; padding: 10px 20px; margin-right: 4px;
        border-top-left-radius: 8px; border-top-right-radius: 8px; min-width: 80px;
    }
    QTabBar::tab:selected { background: #3dd9a8; color: #0a0e14; font-weight: 600; }
    QTabBar::tab:hover:!selected { background: #1c2633; color: #e8eef4; }
    QTableWidget {
        gridline-color: #2d3d52; background-color: #0e141c; alternate-background-color: #121922;
        border: 1px solid #2d3d52; border-radius: 8px;
    }
    QHeaderView::section {
        background-color: #171f2a; color: #e8eef4; padding: 8px; border: none;
        border-bottom: 2px solid #3dd9a8; font-weight: 600;
    }
    QTableWidget::item:selected { background-color: #243548; color: #e8eef4; }
    QTextEdit, QPlainTextEdit {
        background-color: #0c1118; border: 1px solid #2d3d52; border-radius: 8px;
        padding: 10px; font-family: Consolas, monospace; font-size: 12px;
    }
    QScrollBar:vertical { background: #0e141c; width: 12px; margin: 0; border-radius: 6px; }
    QScrollBar::handle:vertical { background: #2d3d52; min-height: 28px; border-radius: 6px; }
    QScrollBar::handle:vertical:hover { background: #3dd9a8; }
    QCheckBox { spacing: 8px; color: #e8eef4; }
    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #2d3d52; background: #0e141c; }
    QCheckBox::indicator:checked { background: #3dd9a8; border-color: #3dd9a8; }
    QFrame#scanHeroBar {
        border: 1px solid #2d3d52;
        border-radius: 14px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #121922, stop:0.55 #101820, stop:1 #0a1016);
    }
    QFrame#topActionsBar {
        background-color: #0e141c;
        border: 1px solid #2d3d52;
        border-radius: 14px;
    }
    QFrame#statusChip {
        background-color: #0e141c; border: 1px solid #2d3d52; border-radius: 10px; min-width: 72px;
    }
    QLabel#chipTitle { color: #8a9caf; font-size: 11px; font-weight: 600; }
    QLabel#heroKicker {
        color: #6b9fff; font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
    }
    QLabel#heroTitle { font-size: 20px; font-weight: 700; color: #e8eef4; }
    QLabel#heroSub { color: #9aaaba; font-size: 12px; line-height: 1.45; }
    QFrame#heroQuoteCard {
        background-color: #0e141c; border: 1px solid #2d3d52; border-radius: 10px;
        min-width: 220px; min-height: 96px;
    }
    QLabel#heroQuoteText {
        color: #c5d2e0; font-size: 12px; line-height: 1.5;
    }
    QLabel#heroQuoteAuthor {
        color: #8eb4d4; font-size: 11px; font-weight: 600;
    }
    QLabel#disclaimerTitle {
        font-size: 15px; font-weight: 700; color: #e8eef4;
    }
    QPushButton#disclaimerAccept:disabled {
        background-color: #1a222c; color: #5c6b7d; border: 1px solid #2d3d52;
    }
    QPushButton#disclaimerAccept:enabled {
        background-color: #3dd9a8; color: #0a0e14; border: none; font-weight: 600;
    }
    QPushButton#disclaimerAccept:enabled:hover { background-color: #52e0b5; }
    QPushButton#disclaimerReject {
        background-color: #1c2633; color: #e8eef4; border: 1px solid #2d3d52;
    }
    QPushButton#disclaimerReject:hover { background-color: #243040; border-color: #ff7b7b; }
    QDialog QTextEdit {
        font-family: "Segoe UI", "Tahoma", sans-serif; font-size: 12px;
    }
    QFrame#welcomeCard {
        background-color: #121922; border: 1px solid #2d3d52; border-radius: 12px;
    }
    QTextEdit#scanLog {
        background-color: #0b1016;
        border: 1px solid #2d3d52;
        border-radius: 12px;
        padding: 12px;
        font-family: Consolas, monospace;
        font-size: 12px;
        selection-background-color: #3dd9a8;
        selection-color: #0a0e14;
    }
    QFrame#oppSection {
        background-color: #0e141c; border: 1px solid #2d3d52; border-radius: 10px;
    }
    QFrame#filterSidebar {
        background-color: #0e141c; border-right: 1px solid #2d3d52;
    }
    QLabel#filterSidebarTitle {
        font-size: 13px; font-weight: 700; color: #9aaaba; padding: 8px 10px 4px 10px;
        border-bottom: 1px solid #2d3d52;
    }
    QGroupBox#filterSidebarGroup {
        font-size: 12px; margin-top: 6px; padding-top: 8px;
        border: 1px solid #2a3545; border-radius: 8px; background-color: #121922;
    }
    QGroupBox#filterSidebarGroup::title {
        subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #8a9caf;
    }
    QLabel#filterSidebarHint {
        color: #7a8aa0; font-size: 11px; margin-bottom: 4px;
    }
    QFrame#resultsFilterPanel {
        background-color: #0e141c; border: 1px solid #2d3d52; border-radius: 12px;
    }
    QFrame#resultsTableShell {
        background-color: #121922; border: 1px solid #2d3d52; border-radius: 12px;
    }
    QLabel#resultsCountLabel {
        color: #9aaaba; font-size: 12px; padding: 4px 2px 0 4px;
    }
    QTableWidget#resultsTable {
        border: none; background-color: #0f1318; gridline-color: #2a3444;
    }
    QTableWidget#resultsTable::item:selected {
        background-color: #355c78; color: #f5fafc;
    }
    QFrame#oppPremiumShell {
        background-color: #060a0e; border: 1px solid #2a4a42; border-radius: 14px;
    }
    QFrame#oppPremiumHero {
        border-radius: 12px;
        border: 1px solid #2d5c4e;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #152a22, stop:0.45 #101c18, stop:1 #0a1210);
    }
    QLabel#oppPremiumBadge {
        color: #5ee0b8; font-size: 10px; font-weight: 700; letter-spacing: 0.18em;
    }
    QLabel#oppPremiumHeroTitle {
        font-size: 20px; font-weight: 700; color: #eef6f2;
    }
    QLabel#oppPremiumHeroSub {
        color: #9db5ad; font-size: 12px; line-height: 1.5;
    }
    QLabel#brandLogo {
        padding: 2px 8px 0 0;
    }
    QPushButton#iconToolButton {
        min-width: 40px;
        min-height: 34px;
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 16px;
    }
    QFrame#detailAnomalyShell {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #121a22, stop:0.5 #101820, stop:1 #0c1218);
        border: 1px solid #2d4a58;
        border-radius: 14px;
    }
    QFrame#detailAnomalyIntro, QFrame#detailAnomalyOverview, QFrame#detailAnomalyBlocks {
        background-color: #0e141c;
        border: 1px solid #2a3d48;
        border-radius: 10px;
    }
    QFrame#detailAnomalyDecision {
        background-color: #152018;
        border: 1px solid #3d7a62;
        border-radius: 10px;
    }
    QFrame#glossaryPremiumShell {
        background-color: #060a0e;
        border: 1px solid #2d4a52;
        border-radius: 16px;
    }
    QFrame#glossaryPremiumHead {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #152028, stop:0.5 #101820, stop:1 #0a1016);
        border-top-left-radius: 14px;
        border-top-right-radius: 14px;
        border-bottom: 1px solid #2d3d52;
    }
    QLabel#glossaryPremiumTitle {
        font-size: 22px;
        font-weight: 800;
        color: #e8eef4;
        letter-spacing: 0.02em;
    }
    QLabel#glossaryPremiumSub {
        font-size: 12px;
        color: #8a9caf;
        line-height: 1.45;
    }
    QFrame#glossaryPremiumAccentBar {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3dd9a8, stop:0.5 #6b9fff, stop:1 #3dd9a8);
        border: none;
    }
    QFrame#glossaryPremiumBody {
        background-color: #0a0e14;
        border-bottom-left-radius: 14px;
        border-bottom-right-radius: 14px;
    }
    QFrame#oppWhyPanel {
        background-color: #121922; border: 1px solid #2d3d52; border-radius: 10px;
    }
    QTabWidget#oppPremiumTabs::pane {
        border: 1px solid #2a4a42; border-radius: 10px; top: -1px; background: #0c1218;
    }
    QTabWidget#oppPremiumTabs QTabBar::tab {
        background: #141c24; color: #8a9caf; padding: 10px 20px; margin-right: 4px;
        border-top-left-radius: 8px; border-top-right-radius: 8px; min-width: 88px;
    }
    QTabWidget#oppPremiumTabs QTabBar::tab:selected {
        background: #1a332c; color: #8af0c8; font-weight: 700;
        border-bottom: 2px solid #3dd9a8;
    }
    QTabWidget#oppPremiumTabs QTabBar::tab:hover:!selected {
        background: #1a242e; color: #e8eef4;
    }
    QTableWidget#oppDataTable {
        gridline-color: #2a3d48; background-color: #0a1016; border: none; border-radius: 8px;
    }
    QTableWidget#oppDataTable QHeaderView::section {
        background-color: #152018; color: #c5ddd4; border-bottom: 2px solid #3d8a72;
    }
    QLabel#welcomeTitle { font-size: 16px; font-weight: 700; color: #e8eef4; }
    QLabel#welcomeBody { color: #b8c5d6; font-size: 12px; line-height: 1.5; }
    QLabel#muted { color: #8a9caf; font-size: 12px; }
    QLabel#chipValue { font-size: 13px; font-weight: 700; }
    /* Dark theme: keep root/background consistently dark. */
    QStackedWidget { background-color: #0a0e14; }
    QScrollArea { border: none; background-color: transparent; }
    QScrollArea > QWidget { background-color: transparent; }
    QAbstractScrollArea::viewport { background-color: transparent; }
    QFrame#detailPanel {
        background-color: #121922; border: 1px solid #2d3d52; border-radius: 10px;
    }
    QFrame#detailTile {
        background-color: #121922; border: 1px solid #2d3d52; border-radius: 10px;
    }
    QLabel#detailTileTitle { color: #8a9caf; font-size: 12px; font-weight: 600; }
    QLabel#detailTileValue { font-size: 20px; font-weight: 700; }
    QLabel#detailTileSub { color: #b8c5d6; font-size: 11px; }
    QLabel#sectionTitle { font-size: 17px; font-weight: 700; color: #e8eef4; }
    QLabel#sectionSub { font-size: 12px; color: #8a9caf; }
    QSplitter::handle { background: #2d3d52; width: 4px; }
    """


def stylesheet_light() -> str:
    return """
    QWidget { font-family: "Segoe UI", "Tahoma", sans-serif; font-size: 13px; color: #1a2330; }
    QMainWindow, QWidget#centralRoot, QDialog { background-color: #eef2f7; }
    QDialog QLabel { color: #1a2330; }
    QMenuBar { background-color: #ffffff; border-bottom: 1px solid #c5d0de; spacing: 4px; }
    QMenuBar::item { padding: 8px 14px; background: transparent; }
    QMenuBar::item:selected { background-color: #e8eef6; }
    QMenu { background-color: #ffffff; border: 1px solid #c5d0de; }
    QMenu::item:selected { background-color: #d4e4f7; }
    QGroupBox {
        border: 1px solid #c5d0de; border-radius: 10px; margin-top: 12px;
        padding: 14px 12px 12px 12px; background-color: #ffffff; font-weight: 600;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #5c6b7d; }
    QPushButton {
        background-color: #f4f7fb; color: #1a2330; border: 1px solid #c5d0de;
        border-radius: 8px; padding: 10px 18px; min-height: 20px;
    }
    QPushButton:hover { background-color: #e8eef6; border-color: #0d9f73; }
    QPushButton:pressed { background-color: #dce4ef; }
    QPushButton#primary { background-color: #0d9f73; color: #ffffff; border: none; font-weight: 600; }
    QPushButton#primary:hover { background-color: #10b37f; }
    QPushButton#accent { background-color: #3d6df0; color: #ffffff; border: none; font-weight: 600; }
    QPushButton#accent:hover { background-color: #557fef; }
    QLineEdit, QComboBox {
        background-color: #ffffff; border: 1px solid #c5d0de; border-radius: 8px;
        padding: 8px 10px; min-height: 22px; selection-background-color: #0d9f73;
        selection-color: #ffffff;
    }
    QComboBox::drop-down { border: none; width: 28px; }
    QComboBox QAbstractItemView {
        background-color: #ffffff; border: 1px solid #c5d0de; selection-background-color: #d4e4f7;
    }
    QProgressBar {
        border: 1px solid #c5d0de; border-radius: 8px; text-align: center;
        background-color: #ffffff; min-height: 18px; color: #1a2330;
    }
    QProgressBar::chunk { background-color: #0d9f73; border-radius: 6px; }
    QTabWidget::pane { border: 1px solid #c5d0de; border-radius: 10px; top: 0px; background: #ffffff; }
    QTabBar::tab {
        background: #e8eef6; color: #5c6b7d; padding: 10px 20px; margin-right: 4px;
        border-top-left-radius: 8px; border-top-right-radius: 8px; min-width: 80px;
    }
    QTabBar::tab:selected { background: #0d9f73; color: #ffffff; font-weight: 600; }
    QTabBar::tab:hover:!selected { background: #f1f5f9; color: #0f172a; }
    QTableWidget {
        gridline-color: #b8c5d4; background-color: #ffffff; alternate-background-color: #f1f5f9;
        border: 1px solid #94a3b8; border-radius: 8px; color: #0f172a;
    }
    QHeaderView::section {
        background-color: #e2e8f0; color: #0f172a; padding: 8px; border: none;
        border-bottom: 2px solid #0d9f73; font-weight: 600;
    }
    QTableWidget::item:selected { background-color: #bfdbfe; color: #0f172a; }
    QTextEdit, QPlainTextEdit {
        background-color: #f8fafc; border: 1px solid #c5d0de; border-radius: 8px;
        padding: 10px; font-family: Consolas, monospace; font-size: 12px;
    }
    QScrollBar:vertical { background: #eef2f7; width: 12px; margin: 0; border-radius: 6px; }
    QScrollBar::handle:vertical { background: #c5d0de; min-height: 28px; border-radius: 6px; }
    QScrollBar::handle:vertical:hover { background: #0d9f73; }
    QCheckBox { spacing: 8px; color: #1a2330; }
    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #c5d0de; background: #fff; }
    QCheckBox::indicator:checked { background: #0d9f73; border-color: #0d9f73; }
    QFrame#scanHeroBar {
        border: 1px solid #c5d0de;
        border-radius: 14px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #ffffff, stop:0.55 #f4f7fb, stop:1 #eef2f7);
    }
    QFrame#topActionsBar {
        background-color: #ffffff;
        border: 1px solid #c5d0de;
        border-radius: 14px;
    }
    QFrame#statusChip {
        background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; min-width: 72px;
    }
    QLabel#chipTitle { color: #475569; font-size: 11px; font-weight: 600; }
    QLabel#heroKicker {
        color: #1d4ed8; font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
    }
    QLabel#heroTitle { font-size: 20px; font-weight: 700; color: #0f172a; }
    QLabel#heroSub { color: #5c6b7d; font-size: 12px; line-height: 1.45; }
    QFrame#heroQuoteCard {
        background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px;
        min-width: 220px; min-height: 96px;
    }
    QLabel#heroQuoteText {
        color: #1e293b; font-size: 12px; line-height: 1.5;
    }
    QLabel#heroQuoteAuthor {
        color: #475569; font-size: 11px; font-weight: 600;
    }
    QFrame#welcomeCard {
        background-color: #ffffff; border: 1px solid #c5d0de; border-radius: 12px;
    }
    QTextEdit#scanLog {
        background-color: #ffffff;
        border: 1px solid #c5d0de;
        border-radius: 12px;
        padding: 12px;
        font-family: Consolas, monospace;
        font-size: 12px;
        selection-background-color: #0d9f73;
        selection-color: #ffffff;
    }
    QFrame#oppSection {
        background-color: #fbfcfe; border: 1px solid #c5d0de; border-radius: 10px;
    }
    QFrame#filterSidebar {
        background-color: #ffffff; border-right: 1px solid #cbd5e1;
    }
    QScrollArea#filterSidebarScroll {
        background-color: #ffffff; border: none;
    }
    QWidget#filterSidebarInner {
        background-color: #ffffff;
    }
    QLabel#filterSidebarTitle {
        font-size: 13px; font-weight: 700; color: #0f172a; padding: 10px 12px 8px 12px;
        border-bottom: 1px solid #e2e8f0; background-color: #ffffff;
    }
    QGroupBox#filterSidebarGroup {
        font-size: 12px; margin-top: 8px; padding-top: 10px; padding-bottom: 8px;
        border: 1px solid #cbd5e1; border-radius: 8px; background-color: #ffffff;
    }
    QGroupBox#filterSidebarGroup::title {
        subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #334155;
    }
    QLabel#filterSidebarHint {
        color: #475569; font-size: 11px; margin-bottom: 4px;
    }
    QFrame#resultsFilterPanel {
        background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px;
    }
    QFrame#resultsTableShell {
        background-color: #ffffff; border: 1px solid #c5d0de; border-radius: 12px;
    }
    QLabel#resultsCountLabel {
        color: #334155; font-size: 12px; padding: 4px 2px 0 4px;
    }
    QTableWidget#resultsTable {
        border: none; background-color: #ffffff; gridline-color: #b8c5d4;
    }
    QTableWidget#resultsTable::item:selected {
        background-color: #bfdbfe; color: #0f172a;
    }
    QFrame#oppPremiumShell {
        background-color: #f6f9fc; border: 1px solid #b8d4c8; border-radius: 14px;
    }
    QFrame#oppPremiumHero {
        border-radius: 12px;
        border: 1px solid #8fcbb3;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #e8f5ef, stop:0.5 #dff0e8, stop:1 #d0e8dc);
    }
    QLabel#oppPremiumBadge {
        color: #0d7a5c; font-size: 10px; font-weight: 700; letter-spacing: 0.18em;
    }
    QLabel#oppPremiumHeroTitle {
        font-size: 20px; font-weight: 700; color: #143d32;
    }
    QLabel#oppPremiumHeroSub {
        color: #1e3d32; font-size: 12px; line-height: 1.55;
    }
    QLabel#brandLogo {
        padding: 2px 8px 0 0;
    }
    QPushButton#iconToolButton {
        min-width: 40px;
        min-height: 34px;
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 16px;
    }
    QFrame#detailAnomalyShell {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #f8fafc, stop:0.5 #f1f5f9, stop:1 #e8eef4);
        border: 1px solid #c5d0de;
        border-radius: 14px;
    }
    QFrame#detailAnomalyIntro, QFrame#detailAnomalyOverview, QFrame#detailAnomalyBlocks {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
    }
    QFrame#detailAnomalyDecision {
        background-color: #ecfdf5;
        border: 1px solid #86efac;
        border-radius: 10px;
    }
    QFrame#glossaryPremiumShell {
        background-color: #ffffff;
        border: 1px solid #c5d0de;
        border-radius: 16px;
    }
    QFrame#glossaryPremiumHead {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #f8fafc, stop:0.5 #f1f5f9, stop:1 #e2e8f0);
        border-top-left-radius: 14px;
        border-top-right-radius: 14px;
        border-bottom: 1px solid #cbd5e1;
    }
    QLabel#glossaryPremiumTitle {
        font-size: 22px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: 0.02em;
    }
    QLabel#glossaryPremiumSub {
        font-size: 12px;
        color: #475569;
        line-height: 1.45;
    }
    QFrame#glossaryPremiumAccentBar {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #0d9f73, stop:0.5 #1d4ed8, stop:1 #0d9f73);
        border: none;
    }
    QFrame#glossaryPremiumBody {
        background-color: #f8fafc;
        border-bottom-left-radius: 14px;
        border-bottom-right-radius: 14px;
    }
    QFrame#oppWhyPanel {
        background-color: #ffffff; border: 1px solid #c5d0de; border-radius: 10px;
    }
    QFrame#oppWhyPanel QAbstractScrollArea::viewport { background-color: #ffffff; }
    QFrame#oppWhyPanel QScrollArea > QWidget { background-color: #ffffff; }
    QFrame#oppWhyPanel QScrollArea { background-color: #ffffff; }
    QFrame#oppWhyPanel QWidget { background-color: #ffffff; }
    QTabWidget#oppPremiumTabs::pane {
        border: 1px solid #b8d4c8; border-radius: 10px; top: -1px; background: #ffffff;
    }
    QTabWidget#oppPremiumTabs { background-color: #ffffff; }
    QTabWidget#oppPremiumTabs QWidget { background-color: #ffffff; }
    QTabWidget#oppPremiumTabs QTabBar::tab {
        background: #e8f0ec; color: #5c6b7d; padding: 10px 20px; margin-right: 4px;
        border-top-left-radius: 8px; border-top-right-radius: 8px; min-width: 88px;
    }
    QTabWidget#oppPremiumTabs QTabBar::tab:selected {
        background: #ffffff; color: #0d7a5c; font-weight: 700;
        border-bottom: 2px solid #0d9f73;
    }
    QTabWidget#oppPremiumTabs QTabBar::tab:hover:!selected {
        background: #f0f6f3; color: #1a2330;
    }
    QTableWidget#oppDataTable {
        gridline-color: #94a3b8; background-color: #ffffff; border: none; border-radius: 8px;
        color: #0f172a;
    }
    QTableWidget#oppDataTable QAbstractScrollArea::viewport { background-color: #ffffff; }
    QTableWidget#oppDataTable::item { background-color: #ffffff; color: #0f172a; }
    QTableWidget#oppDataTable::item:alternate { background-color: #f8fafc; }
    QTableWidget#oppDataTable QHeaderView::section {
        background-color: #dcfce7; color: #0f172a; border-bottom: 2px solid #0d9f73;
    }
    QLabel#welcomeTitle { font-size: 16px; font-weight: 700; color: #0f172a; }
    QLabel#welcomeBody { color: #1e293b; font-size: 12px; line-height: 1.55; }
    QLabel#muted { color: #475569; font-size: 12px; }
    QLabel#chipValue { font-size: 13px; font-weight: 700; color: #0f172a; }
    /* Light theme: avoid dark "bleed-through" under scroll/tab pages. */
    QStackedWidget { background-color: #eef2f7; }
    QTabWidget::pane { background-color: #ffffff; }
    QScrollArea { border: none; background-color: #eef2f7; }
    /* Ensure scroll viewports are solid in light theme (no dark seep). */
    QAbstractScrollArea::viewport { background-color: #ffffff; }
    QScrollArea > QWidget { background-color: #ffffff; }
    QScrollArea QWidget { color: #1a2330; }
    /* Detail view: force scroll surfaces to light colors */
    QScrollArea#detailScroll { background-color: #eef2f7; }
    QScrollArea#detailScroll QAbstractScrollArea::viewport { background-color: #eef2f7; }
    QWidget#detailScrollInner { background-color: #eef2f7; }
    QFrame#detailPanel {
        background-color: #ffffff; border: 1px solid #c5d0de; border-radius: 10px;
    }
    QFrame#detailTile {
        background-color: #ffffff; border: 1px solid #c5d0de; border-radius: 10px;
    }
    QLabel#detailTileTitle { color: #475569; font-size: 12px; font-weight: 600; }
    QLabel#detailTileValue { font-size: 20px; font-weight: 700; color: #0f172a; }
    QLabel#detailTileSub { color: #475569; font-size: 11px; }
    QLabel#sectionTitle { font-size: 17px; font-weight: 700; color: #0f172a; }
    QLabel#sectionSub { font-size: 12px; color: #334155; }
    QSplitter::handle { background: #c5d0de; width: 4px; }
    """
