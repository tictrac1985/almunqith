"""Step 3: choose the destination folder (must not be the source drive)."""
import os
import shutil

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFileDialog)

from almunqith.ui.i18n import tr

_MIN_FREE = 200 * 1024 * 1024


class DestPage(QWidget):
    selection_changed = Signal()

    def __init__(self):
        super().__init__()
        self.path = None
        self._source_drive = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._hint = QLabel()
        self._hint.setObjectName("subtitle")
        row = QHBoxLayout()
        self._choose = QPushButton()
        self._choose.clicked.connect(self.choose)
        self._path_label = QLabel("—")
        self._path_label.setObjectName("subtitle")
        row.addWidget(self._choose)
        row.addWidget(self._path_label, 1)
        self._status = QLabel()
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addSpacing(10)
        layout.addLayout(row)
        layout.addWidget(self._status)
        layout.addStretch(1)
        self.retranslate()

    def retranslate(self):
        self._title.setText(tr("dest_question"))
        self._hint.setText(tr("dest_hint"))
        self._choose.setText(tr("choose_folder"))
        self._update_status()

    def set_source_drive(self, letter):
        self._source_drive = (letter or "").rstrip(":").upper() or None

    def choose(self):
        folder = QFileDialog.getExistingDirectory(self, tr("choose_folder"))
        if folder:
            self.set_path(folder)

    def set_path(self, folder):
        self.path = folder
        self._path_label.setText(folder)
        self._update_status()
        self.selection_changed.emit()

    def _problem(self):
        if not self.path:
            return None
        drive = os.path.splitdrive(self.path)[0].rstrip(":").upper()
        if self._source_drive and drive == self._source_drive:
            return "dest_same_drive"
        # the chosen folder may not exist yet; check the nearest existing parent
        probe = self.path
        while probe and not os.path.isdir(probe):
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        try:
            if shutil.disk_usage(probe).free < _MIN_FREE:
                return "dest_low_space"
        except OSError:
            return "dest_low_space"
        return None

    def _update_status(self):
        problem = self._problem()
        if self.path is None:
            self._status.setText("")
        elif problem:
            self._status.setObjectName("badstatus")
            self._status.setText(tr(problem))
        else:
            self._status.setObjectName("okstatus")
            self._status.setText(tr("dest_ok"))
        self._status.setStyleSheet("")   # re-evaluate object-name styling
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def enter(self):
        self._update_status()

    def can_advance(self) -> bool:
        return self.path is not None and self._problem() is None
