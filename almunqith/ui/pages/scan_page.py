"""Step 4: live deep-scan progress."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QProgressBar, QListWidget, QListWidgetItem)

from almunqith.ui.i18n import tr
from almunqith.ui.worker import ScanWorker

_MAX_THUMBS = 40


class ScanPage(QWidget):
    scan_done = Signal(list)

    def __init__(self):
        super().__init__()
        self.findings = []
        self._counts = {"photos": 0, "videos": 0}
        self._worker = None
        self._reader = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._hint = QLabel()
        self._hint.setObjectName("subtitle")
        self._bar = QProgressBar()
        self._bar.setRange(0, 1000)
        counters = QHBoxLayout()
        self._c_photos = QLabel()
        self._c_videos = QLabel()
        for w in (self._c_photos, self._c_videos):
            w.setStyleSheet("font-size: 15px; font-weight: bold;")
            counters.addWidget(w)
        counters.addStretch(1)
        self._thumbs = QListWidget()
        self._thumbs.setFlow(QListWidget.LeftToRight)
        self._thumbs.setFixedHeight(110)
        self._thumbs.setIconSize(QPixmap(88, 88).size())
        self._log = QListWidget()
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addWidget(self._bar)
        layout.addLayout(counters)
        layout.addWidget(self._thumbs)
        layout.addWidget(self._log, 1)
        self.retranslate()

    def retranslate(self):
        self._title.setText(tr("scan_title"))
        self._hint.setText(tr("scan_hint"))
        self._refresh_counters()

    def _refresh_counters(self):
        self._c_photos.setText(f"🖼️ {tr('counter_photos')}: {self._counts['photos']}")
        self._c_videos.setText(f"🎬 {tr('counter_videos')}: {self._counts['videos']}")

    def start(self, source_factory, categories, reader=None):
        self.findings = []
        self._counts = {"photos": 0, "videos": 0}
        self._reader = reader
        self._thumbs.clear()
        self._log.clear()
        self._bar.setValue(0)
        self._refresh_counters()
        self._worker = ScanWorker(source_factory, categories)
        self._worker.progress.connect(self._on_progress)
        self._worker.found.connect(self._on_found)
        self._worker.log.connect(self._on_log)
        self._worker.finished_scan.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, done, total):
        if total:
            self._bar.setValue(int(done / total * 1000))

    def _on_found(self, finding):
        cat = finding.signature.category
        if cat in self._counts:
            self._counts[cat] += 1
            self._refresh_counters()
        if (cat == "photos" and finding.complete and self._reader
                and self._thumbs.count() < _MAX_THUMBS):
            data = self._reader(finding.offset, min(finding.size, 200_000))
            img = QImage.fromData(data)
            if not img.isNull():
                item = QListWidgetItem()
                item.setIcon(QPixmap.fromImage(
                    img.scaled(88, 88, Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)))
                self._thumbs.addItem(item)

    def _on_log(self, key, kw):
        self._log.addItem(tr("ev_" + key, **kw))
        self._log.scrollToBottom()

    def _on_finished(self, findings):
        self.findings = findings
        self._bar.setValue(1000)
        self.scan_done.emit(findings)

    def enter(self):
        pass

    def can_advance(self) -> bool:
        return True
