"""Step 5: results gallery with selection and extraction."""
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTabWidget, QListWidget,
                               QListWidgetItem, QCheckBox)

from almunqith.ui.i18n import tr
from almunqith.ui.worker import ExtractWorker, RebuildWorker

_CAT_ICON = {"photos": "🖼️", "videos": "🎬", "documents": "📄",
             "audio": "🎵", "archives": "🗜️"}


class ResultsPage(QWidget):
    extract_done = Signal(dict)
    extract_requested = Signal()

    def __init__(self):
        super().__init__()
        self._reader = None
        self._lists: dict[str, QListWidget] = {}
        self._worker = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._hint = QLabel()
        self._hint.setObjectName("subtitle")
        self._tabs = QTabWidget()
        self._rebuild_chk = QCheckBox()
        self._rebuild_chk.setChecked(False)
        self._rebuild_chk.hide()

        bottom = QHBoxLayout()
        self._select_all = QCheckBox()
        self._select_all.setChecked(True)
        self._select_all.stateChanged.connect(self._toggle_all)
        self._status = QLabel()
        self._status.setObjectName("okstatus")
        self._extract_btn = QPushButton()
        self._extract_btn.setObjectName("success")
        self._extract_btn.clicked.connect(self.extract_requested)
        self._open_btn = QPushButton()
        self._open_btn.setObjectName("primary")
        self._open_btn.hide()
        bottom.addWidget(self._select_all)
        bottom.addWidget(self._status, 1)
        bottom.addWidget(self._open_btn)
        bottom.addWidget(self._extract_btn)
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addWidget(self._tabs, 1)
        layout.addWidget(self._rebuild_chk)
        layout.addLayout(bottom)
        self._last_dest = None
        self._rebuild_worker = None
        self._pending_rebuild = False
        self._rebuild_available = False
        self._open_btn.clicked.connect(self._open_folder)
        self.retranslate()

    def retranslate(self):
        self._title.setText(tr("results_title"))
        self._hint.setText(tr("results_hint"))
        self._select_all.setText(tr("select_all"))
        self._extract_btn.setText(tr("extract_selected"))
        self._open_btn.setText(tr("open_folder"))
        self._rebuild_chk.setText(tr("rebuild_videos"))

    def load(self, findings, reader=None):
        self._reader = reader
        self._tabs.clear()
        self._lists.clear()
        by_cat: dict[str, list] = {}
        for f in findings:
            by_cat.setdefault(f.signature.category, []).append(f)
        for cat, items in by_cat.items():
            lst = QListWidget()
            lst.setViewMode(QListWidget.IconMode)
            lst.setIconSize(QPixmap(128, 128).size())
            lst.setResizeMode(QListWidget.Adjust)
            lst.setSpacing(8)
            for f in items:
                it = QListWidgetItem()
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Checked)
                it.setData(Qt.UserRole, f)
                label = f"{f.signature.name}"
                if not f.complete:
                    label += f" ({tr('partial_tag')})"
                it.setText(label)
                if cat == "photos" and reader:
                    data = reader(f.offset, min(f.size, 200_000))
                    img = QImage.fromData(data)
                    if not img.isNull():
                        it.setIcon(QPixmap.fromImage(img.scaled(
                            128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                lst.addItem(it)
            self._lists[cat] = lst
            icon = _CAT_ICON.get(cat, "📁")
            self._tabs.addTab(lst, f"{icon} {tr('cat_' + cat)} ({len(items)})"
                              if ("cat_" + cat) else f"{icon} {cat} ({len(items)})")
        # Offer MJPEG video rebuild when video findings exist, or when there
        # are many photo findings — camera video frames carve as JPEGs, so a
        # large photo count often means fragmented Motion-JPEG video.
        many_photos = len(by_cat.get("photos", [])) >= 20
        self._rebuild_available = ("videos" in by_cat or many_photos)
        self._rebuild_chk.setVisible(self._rebuild_available)

    def _toggle_all(self, state):
        st = Qt.Checked if state else Qt.Unchecked
        for lst in self._lists.values():
            for i in range(lst.count()):
                lst.item(i).setCheckState(st)

    def selected_findings(self):
        out = []
        for lst in self._lists.values():
            for i in range(lst.count()):
                it = lst.item(i)
                if it.checkState() == Qt.Checked:
                    out.append(it.data(Qt.UserRole))
        return out

    def extract_to(self, dest, source_factory, source_drive=None):
        self._last_dest = dest
        self._source_factory = source_factory
        self._extract_btn.setEnabled(False)
        self._status.setText(tr("extracting"))
        self._pending_rebuild = (self._rebuild_available
                                 and self._rebuild_chk.isChecked())
        self._worker = ExtractWorker(source_factory, self.selected_findings(),
                                     dest, source_drive=source_drive)
        self._worker.finished_extract.connect(self._on_extracted)
        self._worker.start()

    def _on_extracted(self, summary):
        self._last_summary = summary
        if self._pending_rebuild and self._source_factory:
            self._status.setText(tr("rebuilding"))
            out = os.path.join(self._last_dest, "Videos_Rebuilt")
            self._rebuild_worker = RebuildWorker(self._source_factory, out)
            self._rebuild_worker.finished_rebuild.connect(self._on_rebuilt)
            self._rebuild_worker.start()
            return
        self._finish(summary)

    def _on_rebuilt(self, videos):
        self._finish(self._last_summary, rebuilt=len(videos))

    def _finish(self, summary, rebuilt=0):
        if rebuilt:
            self._status.setText(tr("saved_and_rebuilt", n=summary["saved"],
                                    v=rebuilt))
        else:
            self._status.setText(tr("saved_summary", n=summary["saved"]))
        self._extract_btn.setEnabled(True)
        self._open_btn.show()
        self.extract_done.emit(summary)

    def _open_folder(self):
        if self._last_dest and os.path.isdir(self._last_dest):
            os.startfile(self._last_dest)   # noqa: S606 - user-initiated

    def enter(self):
        pass

    def can_advance(self) -> bool:
        return True
