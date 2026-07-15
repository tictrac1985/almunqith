"""AlMunqith main window.

A home screen offers two services:
  • Recover files  — the five-step recovery wizard (drive/types/dest/scan/results)
  • Securely wipe  — the three-step wipe flow (drive/confirm/progress)

The recovery flow is preserved intact (self.pages, go_next/go_back, etc.).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QStackedWidget, QFrame)

from almunqith.ui.i18n import tr, set_language, get_language, is_rtl
from almunqith.ui.pages.start_page import StartPage
from almunqith.ui.pages.drive_page import DrivePage
from almunqith.ui.pages.types_page import TypesPage
from almunqith.ui.pages.dest_page import DestPage
from almunqith.ui.pages.scan_page import ScanPage
from almunqith.ui.pages.results_page import ResultsPage
from almunqith.ui.pages.wipe_drive_page import WipeDrivePage
from almunqith.ui.pages.wipe_confirm_page import WipeConfirmPage
from almunqith.ui.pages.wipe_progress_page import WipeProgressPage
from almunqith.core.source import DiskImage, RawDevice
from almunqith.core import devices

_STEP_KEYS = ["step_drive", "step_types", "step_dest", "step_scan", "step_results"]

# extra QSS for the two big home-screen service cards
_HOME_QSS = """
QPushButton#servicecard { background: #1c2333; border: 1px solid #2a3040;
    border-radius: 16px; padding: 22px; font-size: 15px; color: #eef2ff; }
QPushButton#servicecard:hover { border: 2px solid #3b82f6; background: #1d2a45; }
"""


class Wizard(QMainWindow):
    def __init__(self, drives_provider=None, source_override=None,
                 wipe_func_override=None):
        super().__init__()
        self._drives_provider = drives_provider or devices.list_drives
        self._source_override = source_override
        self._wipe_override = wipe_func_override
        self.resize(880, 640)
        self.setStyleSheet(_HOME_QSS)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        # ---- top bar (always visible) ----
        topbar = QHBoxLayout()
        topbar.setContentsMargins(16, 12, 16, 6)
        self._brand = QLabel()
        self._brand.setStyleSheet("font-size: 17px; font-weight: bold;")
        self._brand.setCursor(Qt.PointingHandCursor)
        self._lang_btn = QPushButton()
        self._lang_btn.clicked.connect(self._toggle_language)
        topbar.addWidget(self._brand)
        topbar.addStretch(1)
        topbar.addWidget(self._lang_btn)
        root.addLayout(topbar)

        # ---- top-level screens: home / recovery / wipe ----
        self.root_stack = QStackedWidget()
        self.start_page = StartPage()
        self.start_page.recover_requested.connect(self._go_recovery)
        self.start_page.wipe_requested.connect(self._go_wipe)
        self._recovery = self._build_recovery()
        self._wipe = self._build_wipe()
        self.root_stack.addWidget(self.start_page)     # 0
        self.root_stack.addWidget(self._recovery)      # 1
        self.root_stack.addWidget(self._wipe)          # 2
        root.addWidget(self.root_stack, 1)

        self.retranslate()
        self._update_chips()
        self._sync_nav()

    # ================= recovery flow =================
    def _build_recovery(self) -> QWidget:
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)

        self._chips_row = QHBoxLayout()
        self._chips_row.setContentsMargins(16, 4, 16, 8)
        self._chips_row.setSpacing(6)
        home1 = QPushButton()
        home1.setFlat(True)
        home1.clicked.connect(self._go_home)
        self._home_btn1 = home1
        self._chips_row.addWidget(home1)
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
        v.addWidget(chips_frame)

        self.pages = QStackedWidget()
        self.drive_page = DrivePage(self._drives_provider)
        self.types_page = TypesPage()
        self.dest_page = DestPage()
        self.scan_page = ScanPage()
        self.results_page = ResultsPage()
        for p in (self.drive_page, self.types_page, self.dest_page,
                  self.scan_page, self.results_page):
            self.pages.addWidget(p)
        v.addWidget(self.pages, 1)

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
        v.addLayout(nav)

        self.drive_page.selection_changed.connect(self._sync_nav)
        self.types_page.selection_changed.connect(self._sync_nav)
        self.dest_page.selection_changed.connect(self._sync_nav)
        self.scan_page.scan_done.connect(self._on_scan_done)
        self.results_page.extract_requested.connect(self._do_extract)
        self.results_page.extract_done.connect(lambda s: self._sync_nav())
        return container

    def _do_extract(self):
        """Run extraction of the selected findings to the chosen destination."""
        dest = self.dest_page.path
        if not dest:
            return
        self.results_page.extract_to(dest, self._source_factory(),
                                     source_drive=self._source_drive_letter())

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

    def current_index(self) -> int:
        return self.pages.currentIndex()

    def _current_page(self):
        return self.pages.currentWidget()

    def go_next(self):
        page = self._current_page()
        if not page.can_advance():
            return
        idx = self.pages.currentIndex()
        if idx == 2:
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
        if idx == 3:
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
        self._next_btn.setVisible(idx < 3)

    def _update_chips(self):
        cur = self.pages.currentIndex()
        for i, chip in enumerate(self._chips):
            chip.setText(tr(_STEP_KEYS[i]))
            chip.setProperty("active", i == cur)
            chip.style().unpolish(chip)
            chip.style().polish(chip)

    # ================= wipe flow =================
    def _build_wipe(self) -> QWidget:
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)

        toprow = QHBoxLayout()
        toprow.setContentsMargins(16, 4, 16, 8)
        self._home_btn2 = QPushButton()
        self._home_btn2.setFlat(True)
        self._home_btn2.clicked.connect(self._go_home)
        toprow.addWidget(self._home_btn2)
        toprow.addStretch(1)
        wf = QFrame()
        wf.setLayout(toprow)
        v.addWidget(wf)

        self.wipe_pages = QStackedWidget()
        self.wipe_drive_page = WipeDrivePage(self._drives_provider)
        self.wipe_confirm_page = WipeConfirmPage()
        self.wipe_progress_page = WipeProgressPage()
        for p in (self.wipe_drive_page, self.wipe_confirm_page,
                  self.wipe_progress_page):
            self.wipe_pages.addWidget(p)
        v.addWidget(self.wipe_pages, 1)

        nav = QHBoxLayout()
        nav.setContentsMargins(16, 6, 16, 14)
        self._wback_btn = QPushButton()
        self._wback_btn.clicked.connect(self._wipe_back)
        self._wnext_btn = QPushButton()
        self._wnext_btn.setObjectName("primary")
        self._wnext_btn.clicked.connect(self._wipe_next)
        nav.addWidget(self._wback_btn)
        nav.addStretch(1)
        nav.addWidget(self._wnext_btn)
        v.addLayout(nav)

        self.wipe_drive_page.selection_changed.connect(self._sync_wipe_nav)
        self.wipe_confirm_page.confirm_changed.connect(self._sync_wipe_nav)
        self.wipe_progress_page.wipe_done.connect(lambda s: self._sync_wipe_nav())
        return container

    def _wipe_next(self):
        idx = self.wipe_pages.currentIndex()
        if idx == 0:
            if not self.wipe_drive_page.can_advance():
                return
            self.wipe_confirm_page.set_drive(self.wipe_drive_page.selected)
            self.wipe_drive_page.leave()
            self.wipe_pages.setCurrentIndex(1)
        elif idx == 1:
            if not self.wipe_confirm_page.can_start():
                return
            self.wipe_pages.setCurrentIndex(2)
            self.wipe_progress_page.start(
                self.wipe_drive_page.selected,
                self.wipe_confirm_page.passes(),
                wipe_func=self._wipe_override)
        self._sync_wipe_nav()

    def _wipe_back(self):
        idx = self.wipe_pages.currentIndex()
        if idx == 0:
            self._go_home()
            return
        if idx == 2:                       # don't allow leaving mid-wipe
            return
        self.wipe_pages.setCurrentIndex(idx - 1)
        if idx - 1 == 0:
            self.wipe_drive_page.enter()
        self._sync_wipe_nav()

    def _sync_wipe_nav(self):
        idx = self.wipe_pages.currentIndex()
        self._wback_btn.setEnabled(idx != 2)
        if idx == 0:
            self._wnext_btn.setText(tr("next"))
            self._wnext_btn.setEnabled(self.wipe_drive_page.can_advance())
            self._wnext_btn.setVisible(True)
        elif idx == 1:
            self._wnext_btn.setText(tr("wipe_start"))
            self._wnext_btn.setEnabled(self.wipe_confirm_page.can_start())
            self._wnext_btn.setVisible(True)
        else:
            self._wnext_btn.setVisible(False)

    # ================= screen switching =================
    def _go_home(self):
        self.root_stack.setCurrentIndex(0)
        self.start_page.enter()

    def _go_recovery(self):
        self.pages.setCurrentIndex(0)
        self.root_stack.setCurrentIndex(1)
        self.drive_page.enter()
        self._update_chips()
        self._sync_nav()

    def _go_wipe(self):
        self.wipe_pages.setCurrentIndex(0)
        self.root_stack.setCurrentIndex(2)
        self.wipe_drive_page.enter()
        self._sync_wipe_nav()

    # ================= language =================
    def _toggle_language(self):
        set_language("en" if get_language() == "ar" else "ar")
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
        self._home_btn1.setText(tr("back_home"))
        self._home_btn2.setText(tr("back_home"))
        self._wback_btn.setText(tr("back"))
        self.start_page.retranslate()
        for p in (self.drive_page, self.types_page, self.dest_page,
                  self.scan_page, self.results_page,
                  self.wipe_drive_page, self.wipe_confirm_page,
                  self.wipe_progress_page):
            p.retranslate()
        self._update_chips()
        self._sync_wipe_nav()
