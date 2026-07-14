"""Wipe step 3: run the secure wipe with progress, then show the result."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar,
                               QListWidget)

from almunqith.ui.i18n import tr
from almunqith.ui.worker import WipeWorker


class WipeProgressPage(QWidget):
    wipe_done = Signal(dict)

    def __init__(self):
        super().__init__()
        self._worker = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._bar = QProgressBar()
        self._bar.setRange(0, 1000)
        self._status = QLabel()
        self._status.setObjectName("subtitle")
        self._log = QListWidget()
        layout.addWidget(self._title)
        layout.addWidget(self._bar)
        layout.addWidget(self._status)
        layout.addWidget(self._log, 1)
        self.retranslate()

    def retranslate(self):
        self._title.setText(tr("wipe_running"))

    def start(self, drive_info, passes, wipe_func=None):
        self._bar.setValue(0)
        self._log.clear()
        self._status.setText("")
        self._title.setText(tr("wipe_running"))
        self._worker = WipeWorker(drive_info, passes, wipe_func=wipe_func)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.finished_wipe.connect(self._on_done)
        self._worker.start()

    def _on_progress(self, done, total, idx, name):
        if total:
            self._bar.setValue(int(done / total * 1000))
        self._status.setText(tr("wipe_pass", idx=idx + 1,
                                total=self._passes_count(), name=name))

    def _passes_count(self):
        return getattr(self, "_npasses", 3)

    def _on_log(self, key, kw):
        if key == "wipe_started":
            self._npasses = kw.get("passes", 3)
        if key == "formatting":
            self._status.setText(tr("wipe_formatting"))
        text = {
            "wipe_started": tr("wipe_running"),
            "formatting": tr("wipe_formatting"),
        }.get(key)
        if text:
            self._log.addItem(text)
            self._log.scrollToBottom()

    def _on_done(self, summary):
        self._bar.setValue(1000)
        ok = summary.get("ok", False)
        self._title.setText(tr("wipe_done") if ok else tr("wipe_failed"))
        self._status.setText("")
        self.wipe_done.emit(summary)

    def enter(self):
        pass
