"""Step 1: pick the affected drive."""
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QButtonGroup)

from almunqith.ui.i18n import tr

_ICONS = {"USB": "💾", "SD": "💾", "NVMe": "🗄️", "SATA": "🗄️", "RAID": "🗄️"}


class DrivePage(QWidget):
    selection_changed = Signal()

    def __init__(self, drives_provider):
        super().__init__()
        self._provider = drives_provider
        self.selected = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._hint = QLabel()
        self._hint.setObjectName("subtitle")
        self._warn = QLabel()
        self._warn.setObjectName("warning")
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(12)
        self._footer = QLabel()
        self._footer.setObjectName("subtitle")
        self._layout.addWidget(self._title)
        self._layout.addWidget(self._hint)
        self._layout.addWidget(self._warn)
        self._layout.addSpacing(8)
        self._layout.addLayout(self._cards_row)
        self._layout.addStretch(1)
        self._layout.addWidget(self._footer)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.refresh)
        self.retranslate()
        self.refresh()

    def retranslate(self):
        self._title.setText(tr("drive_question"))
        self._hint.setText(tr("drive_hint"))
        self._warn.setText(tr("drive_warning"))
        self._footer.setText(tr("auto_refresh"))

    def _card_text(self, d):
        gb = d.size / 1_000_000_000
        letters = " ".join(f"({x}:)" for x in d.letters)
        bus = tr("usb") if d.bus == "USB" else tr("internal")
        tag = f"\n{tr('system_disk_tag')}" if d.is_system else ""
        icon = _ICONS.get(d.bus, "🔌")
        return f"{icon}  {d.friendly} {letters}\n{gb:.1f} {tr('gb')} • {bus}{tag}"

    def refresh(self):
        try:
            drives = self._provider()
        except Exception:
            return
        selected_path = self.selected.path if self.selected else None
        while self._cards_row.count():
            item = self._cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for btn in self._group.buttons():
            self._group.removeButton(btn)
        for d in drives:
            btn = QPushButton(self._card_text(d))
            btn.setObjectName("card")
            btn.setCheckable(True)
            btn.setMinimumWidth(210)
            btn.clicked.connect(lambda _=False, drv=d: self.select_drive(drv))
            self._group.addButton(btn)
            self._cards_row.addWidget(btn)
            if d.path == selected_path:
                btn.setChecked(True)
        self._cards_row.addStretch(1)

    def select_drive(self, drive):
        self.selected = drive
        self.selection_changed.emit()

    def enter(self):
        self.refresh()
        self.timer.start()

    def leave(self):
        self.timer.stop()

    def can_advance(self) -> bool:
        return self.selected is not None
