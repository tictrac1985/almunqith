"""Wipe step 2: method choice + hard confirmation (type the drive letter)."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QRadioButton,
                               QLineEdit, QButtonGroup)

from almunqith.ui.i18n import tr
from almunqith.core.wipe import PASSES_3, PASSES_1


class WipeConfirmPage(QWidget):
    confirm_changed = Signal()

    def __init__(self):
        super().__init__()
        self._drive = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._warn = QLabel()
        self._warn.setObjectName("warning")
        self._warn.setWordWrap(True)
        self._target = QLabel()
        self._target.setObjectName("badstatus")
        self._target.setStyleSheet("font-size: 15px; font-weight: bold;")

        self._method_label = QLabel()
        self._m3 = QRadioButton()
        self._m1 = QRadioButton()
        self._m3.setChecked(True)
        self._methods = QButtonGroup(self)
        self._methods.addButton(self._m3)
        self._methods.addButton(self._m1)

        self._ssd = QLabel()
        self._ssd.setObjectName("subtitle")
        self._ssd.setWordWrap(True)

        self._prompt = QLabel()
        self._entry = QLineEdit()
        self._entry.setMaximumWidth(120)
        self._entry.textChanged.connect(lambda _: self.confirm_changed.emit())

        layout.addWidget(self._title)
        layout.addWidget(self._warn)
        layout.addWidget(self._target)
        layout.addSpacing(6)
        layout.addWidget(self._method_label)
        layout.addWidget(self._m3)
        layout.addWidget(self._m1)
        layout.addWidget(self._ssd)
        layout.addStretch(1)
        layout.addWidget(self._prompt)
        layout.addWidget(self._entry)
        self.retranslate()

    def retranslate(self):
        self._title.setText(tr("wipe_confirm_title"))
        self._warn.setText(tr("wipe_confirm_warn"))
        self._method_label.setText(tr("wipe_method"))
        self._m3.setText(tr("wipe_method_3"))
        self._m1.setText(tr("wipe_method_1"))
        self._ssd.setText(tr("wipe_ssd_note"))
        self._refresh_target()

    def set_drive(self, drive):
        self._drive = drive
        self._entry.clear()
        self._refresh_target()

    def _letter(self):
        if self._drive and self._drive.letters:
            return self._drive.letters[0].upper()
        return None

    def _refresh_target(self):
        if not self._drive:
            self._target.setText("")
            self._prompt.setText("")
            return
        gb = self._drive.size / 1_000_000_000
        letters = " ".join(f"({x}:)" for x in self._drive.letters)
        self._target.setText(f"{self._drive.friendly} {letters} — {gb:.1f} {tr('gb')}")
        letter = self._letter() or "?"
        self._prompt.setText(tr("wipe_type_letter", letter=letter))

    def passes(self):
        return PASSES_3 if self._m3.isChecked() else PASSES_1

    def can_start(self) -> bool:
        letter = self._letter()
        if not letter:
            return False
        return self._entry.text().strip().upper().rstrip(":") == letter

    def enter(self):
        pass
