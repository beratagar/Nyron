# -*- coding: utf-8 -*-
"""Arka planda analiz çalıştırma."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """StockAnalyzer.analyze iş parçacığında çalışır; arayüz bloklanmaz."""

    progress = Signal(int, int)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, analyzer, parent=None):
        super().__init__(parent)
        self._analyzer = analyzer

    def run(self):
        try:

            def cb(cur, total):
                self.progress.emit(cur, total)

            results = self._analyzer.analyze(progress_callback=cb)
            self.finished_ok.emit(results)
        except Exception as exc:
            logger.exception("Analiz iş parçacığı hatası")
            self.failed.emit(str(exc))
