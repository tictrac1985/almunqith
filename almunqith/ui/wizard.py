"""The five-step wizard shell: header, stacked pages, navigation, language."""
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QStackedWidget, QFrame)

from almunqith.ui.i18n import tr, set_language, get_language, is_rtl
from almunqith.ui.pages.drive_page import DrivePage
from almunqith.ui.pages.types_page import TypesPage
from almunqith.ui.pages.dest_page import DestPage
from almunqith.ui.pages.scan_page import ScanPage
from almunqith.ui.pages.results_page import ResultsPage
from almunqith.core.source import DiskImage, RawDevice
from almunqith.core import devices

_STEP_KEYS = ["step_drive", "step_types", "step_dest", "step_scan", "step_results"]


class Wizard(QMainWindow):
    def __init__(self, drives_provider=None, source_override=None):
        super().__init__()
        self._drives_provider = drives_provider or devices.list_drives
        self._source_override = source_override      # path to an image file (dev/test)
        self.resize(880, 640)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        # top bar: title + language toggle
        topbar = QHBoxLayout()
        topbar.setContentsMargins(16, 12, 16, 6)
        self._brand = QLabel()
        self._brand.setStyleSheet("font-size: 17px; font-weight: bold;")
        self._lang_btn = QPushButton()
        self._lang_btn.clicked.connect(self._toggle_language)
        topbar.addWidget(self._brand)
        topbar.addStretch(1)
        topbar.addWidget(self._lang_btn)
        root.addLayout(topbar)

        # step chips
        self._chips_row = QHBoxLayout()
        self._chips_row.setContentsMargins(16, 4, 16, 8)
        self._chips_row.setSpacing(6)
        self._chips = []
        for key in _STEP_KEYS:
            chip = QLabel()
            chip.setObjectName("stepchip")
            chip.setAlignment(Qt.AlignCenter)
            self._chips.append(chip)
            self._chips_row.addWidget(chip)
        self._chips_row.addStretch(1)
        chips_frame = QFrame()
        chips_frame.setLayout(self._chips_row)
        root.addWidget(chips_frame)

        # pages
        self.pages = QStackedWidget()
        self.drive_page = DrivePage(self._drives_provider)
        self.types_page = TypesPage()
        self.dest_page = DestPage()
        self.scan_page = ScanPage()
        self.results_page = ResultsPage()
        for p in (self.drive_page, self.types_page, self.dest_page,
                  self.scan_page, self.results_page):
            self.pages.addWidget(p)
        root.addWidget(self.pages, 1)

        # bottom nav
        nav = QHBoxLayout()
        nav.setContentsMargins(16, 6, 16, 14)
        self._back_btn = QPushButton()
        self._back_btn.clicked.connect(self.go_back)
        self._next_btn = QPushButton()
        self._next_btn.setObjectName("primary")
        self._next_btn.clicked.connect(self.go_next)
        nav.addWidget(self._back_btn)
        nav.addStretch(1)
        nav.addWidget(self._next_btn)
        root.addLayout(nav)

        # react to page readiness
        self.drive_page.selection_changed.connect(self._sync_nav)
        self.types_page.selection_changed.connect(self._sync_nav)
        self.dest_page.selection_changed.connect(self._sync_nav)
        self.scan_page.scan_done.connect(self._on_scan_done)
        self.results_page.extract_done.connect(lambda s: self._sync_nav())

        self.retranslate()
        self.drive_page.enter()
        self._update_chips()
        self._sync_nav()

    # ---- source plumbing -------------------------------------------------
    def _source_factory(self):
        if self._source_override:
            path = self._source_override
            return lambda: DiskImage(path)
        drv = self.drive_page.selected
        return lambda: RawDevice(drv.path, drv.size)

    def _reader(self, offset, length):
        src = self._source_factory()()
        try:
            return src.read_at(offset, length)
        finally:
            src.close()

    def _source_drive_letter(self):
        drv = self.drive_page.selected
        if drv and drv.letters:
            return drv.letters[0]
        return None

    # ---- navigation ------------------------------------------------------
    def current_index(self) -> int:
        return self.pages.currentIndex()

    def _current_page(self):
        return self.pages.currentWidget()

    def go_next(self):
        page = self._current_page()
        if not page.can_advance():
            return
        idx = self.pages.currentIndex()
        if idx == 2:                       # leaving destination -> start scan
            self.dest_page.set_source_drive(self._source_drive_letter())
        if idx >= self.pages.count() - 1:
            return
        if hasattr(page, "leave"):
            page.leave()
        self.pages.setCurrentIndex(idx + 1)
        self._enter_current()

    def go_back(self):
        idx = self.pages.currentIndex()
        if idx <= 0:
            return
        page = self._current_page()
        if hasattr(page, "leave"):
            page.leave()
        self.pages.setCurrentIndex(idx - 1)
        self._enter_current()

    def _enter_current(self):
        idx = self.pages.currentIndex()
        page = self._current_page()
        page.enter()
        if idx == 2:
            self.dest_page.set_source_drive(self._source_drive_letter())
        if idx == 3:                       # scan page auto-starts
            self.scan_page.start(self._source_factory(),
                                 self.types_page.categories(),
                                 reader=self._reader)
        self._update_chips()
        self._sync_nav()

    def _on_scan_done(self, findings):
        self.results_page.load(findings, reader=self._reader)
        if self.pages.currentIndex() == 3:
            self.pages.setCurrentIndex(4)
            self.results_page.enter()
            self._update_chips()
            self._sync_nav()

    def _sync_nav(self):
        idx = self.pages.currentIndex()
        self._back_btn.setEnabled(idx > 0)
        last = idx >= self.pages.count() - 1
        self._next_btn.setEnabled(not last and self._current_page().can_advance())
        # on results page the "next" is replaced by extract, handled in page
        self._next_btn.setVisible(idx < 3)

    def _update_chips(self):
        cur = self.pages.currentIndex()
        for i, chip in enumerate(self._chips):
            chip.setText(tr(_STEP_KEYS[i]))
            chip.setProperty("active", i == cur)
            chip.style().unpolish(chip)
            chip.style().polish(chip)

    # ---- language --------------------------------------------------------
    def _toggle_language(self):
        set_language("en" if get_language() == "ar" else "ar")
        app = self.window().windowHandle()
        self.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setLayoutDirection(
            Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(tr("app_title"))
        self._brand.setText("🛟 " + tr("app_title"))
        self._lang_btn.setText(tr("language"))
        self._back_btn.setText(tr("back"))
        self._next_btn.setText(tr("next"))
        for p in (self.drive_page, self.types_page, self.dest_page,
                  self.scan_page, self.results_page):
            p.retranslate()
        self._update_chips()
