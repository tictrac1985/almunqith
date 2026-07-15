"""Wipe step 1: choose the disk to erase. System disks are shown but disabled."""
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QButtonGroup)

from almunqith.ui.i18n import tr

_ICONS = {"USB": "💾", "NVMe": "🗄️", "SATA": "🗄️", "RAID": "🗄️"}


class WipeDrivePage(QWidget):
    selection_changed = Signal()

    def __init__(self, drives_provider):
        super().__init__()
        self._provider = drives_provider
        self.selected = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._hint = QLabel()
        self._hint.setObjectName("subtitle")
        self._danger = QLabel()
        self._danger.setObjectName("badstatus")
        self._danger.setWordWrap(True)
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(12)
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addWidget(self._danger)
        layout.addSpacing(8)
        layout.addLayout(self._cards_row)
        layout.addStretch(1)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._loader = None
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.refresh)
        self.retranslate()
        # drives are loaded asynchronously on enter(), not at construction

    def retranslate(self):
        self._title.setText(tr("wipe_drive_q"))
        self._hint.setText(tr("wipe_drive_hint"))
        self._danger.setText(tr("wipe_danger"))

    def _card_text(self, d):
        gb = d.size / 1_000_000_000
        letters = " ".join(f"({x}:)" for x in d.letters)
        icon = _ICONS.get(d.bus, "🔌")
        if d.is_system:
            return f"{icon}  {d.friendly} {letters}\n{gb:.1f} {tr('gb')}\n{tr('wipe_system_blocked')}"
        return f"{icon}  {d.friendly} {letters}\n{gb:.1f} {tr('gb')}"

    def refresh(self):
        if self._loader is not None and self._loader.isRunning():
            return
        from almunqith.ui.worker import DrivesWorker
        self._loader = DrivesWorker(self._provider)
        self._loader.drives_ready.connect(self._apply)
        self._loader.start()

    def _apply(self, drives):
        sig = tuple((d.path, d.size, tuple(d.letters), d.is_system) for d in drives)
        if sig == getattr(self, "_last_sig", None):
            return
        self._last_sig = sig
        selected_path = self.selected.path if self.selected else None
        while self._cards_row.count():
            item = self._cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for btn in self._group.buttons():
            self._group.removeButton(btn)
        for d in drives:
            blocked = d.is_system or "C" in [x.upper() for x in d.letters]
            btn = QPushButton(self._card_text(d))
            btn.setObjectName("card")
            btn.setCheckable(True)
            btn.setMinimumWidth(210)
            btn.setEnabled(not blocked)
            if not blocked:
                btn.clicked.connect(lambda _=False, drv=d: self.select_drive(drv))
                self._group.addButton(btn)
                if d.path == selected_path:
                    btn.setChecked(True)
            self._cards_row.addWidget(btn)
        self._cards_row.addStretch(1)

    def select_drive(self, drive):
        self.selected = drive
        self.selection_changed.emit()

    def enter(self):
        self.selected = None
        self._last_sig = None
        self.refresh()
        self.timer.start()

    def leave(self):
        self.timer.stop()

    def can_advance(self) -> bool:
        return self.selected is not None
