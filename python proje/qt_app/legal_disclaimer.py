# -*- coding: utf-8 -*-
"""İlk açılış sorumluluk reddi (okudum onayı + kabul / red)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from config import APP
from qt_app.styles import stylesheet_dark

_APP = APP.get("name", "Nyron")

_DISCLAIMER_TITLE = "⚠️ SORUMLULUK REDDİ VE KULLANIM ŞARTLARI"

_DISCLAIMER_BODY = """
Bu uygulama, yalnızca kişisel geliştirme ve eğitim amacıyla oluşturulmuştur. Uygulama içerisinde yer alan tüm veriler, grafikler, göstergeler ve analizler yatırım tavsiyesi niteliği taşımaz.

Bu içerikler Sermaye Piyasası Kurulu (SPK) kapsamında yatırım danışmanlığı olarak değerlendirilemez.

Sunulan bilgiler doğrultusunda alınan tüm yatırım kararları tamamen kullanıcının kendi sorumluluğundadır. Uygulama geliştiricisi; veri hataları, gecikmeler, teknik arızalar veya analiz sonuçlarındaki olası yanlışlıklardan dolayı oluşabilecek hiçbir zarardan sorumlu tutulamaz.

Geçmiş performans verileri gelecekteki sonuçları garanti etmez. Finansal piyasalarda işlem yapmak risklidir ve para kaybı yaşanabilir.

Uygulamayı kullanarak bu şartları okuduğunuzu, anladığınızı ve kabul ettiğinizi beyan etmiş olursunuz.
""".strip()


def show_legal_disclaimer() -> bool:
    """True: kullanıcı kabul etti. False: çıkış."""
    dlg = QDialog()
    dlg.setWindowTitle(f"{_APP} — sorumluluk reddi")
    dlg.setMinimumSize(560, 480)
    dlg.setModal(True)
    dlg.setStyleSheet(stylesheet_dark())
    lay = QVBoxLayout(dlg)
    lay.setSpacing(12)

    title = QLabel(_DISCLAIMER_TITLE)
    title.setObjectName("disclaimerTitle")
    title.setWordWrap(True)

    body = QTextEdit()
    body.setReadOnly(True)
    body.setPlainText(_DISCLAIMER_BODY)
    body.setMinimumHeight(240)

    chk = QCheckBox("Okudum, anladım.")
    chk.setObjectName("disclaimerReadCheck")

    btn_cancel = QPushButton("Reddet ve çık")
    btn_cancel.setObjectName("disclaimerReject")
    btn_ok = QPushButton("Kabul ediyorum")
    btn_ok.setObjectName("disclaimerAccept")
    btn_ok.setEnabled(False)

    chk.stateChanged.connect(lambda _: btn_ok.setEnabled(chk.isChecked()))

    btn_row = QHBoxLayout()
    btn_row.setSpacing(12)
    btn_row.addWidget(btn_cancel)
    btn_row.addStretch(1)
    btn_row.addWidget(btn_ok)

    btn_cancel.clicked.connect(dlg.reject)
    btn_ok.clicked.connect(dlg.accept)

    lay.addWidget(title)
    lay.addWidget(body, 1)
    lay.addWidget(chk)
    lay.addLayout(btn_row)

    dlg.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    return dlg.exec() == QDialog.DialogCode.Accepted
