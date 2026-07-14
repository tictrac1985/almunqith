"""Tiny Arabic/English GUI for the AlMunqith installer (no terminal shown)."""
import os
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                               QProgressBar, QPushButton, QMessageBox)

import installer_main as core

_AR = {
    "title": "تثبيت المنقذ",
    "welcome": "مرحبًا بك في مُثبِّت «المنقذ»",
    "desc": "سيُثبَّت البرنامج لك وحدك (بدون صلاحيات مدير) ويضع اختصارًا على سطح المكتب وقائمة ابدأ.",
    "install": "تثبيت",
    "installing": "جارٍ التثبيت...",
    "done": "🎉 تم التثبيت بنجاح!",
    "launch": "تشغيل البرنامج الآن",
    "close": "إغلاق",
    "uninstall_title": "إزالة المنقذ",
    "uninstall_q": "هل تريد إزالة «المنقذ» من جهازك؟",
    "uninstalling": "جارٍ الإزالة...",
    "uninstalled": "تمت الإزالة.",
    "yes": "نعم، أزل",
}


def tr(k):
    return _AR.get(k, k)


class Job(QThread):
    step = Signal(int, str)
    done = Signal(str)

    def __init__(self, uninstall=False):
        super().__init__()
        self._uninstall = uninstall

    def run(self):
        if self._uninstall:
            core.do_uninstall(lambda p, m: self.step.emit(p, m))
            self.done.emit("")
        else:
            exe = core.do_install(lambda p, m: self.step.emit(p, m))
            self.done.emit(exe)


class InstallerWindow(QWidget):
    def __init__(self, uninstall=False):
        super().__init__()
        self._uninstall = uninstall
        self._app_exe = None
        self.setWindowTitle(tr("uninstall_title") if uninstall else tr("title"))
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(460, 240)
        self.setStyleSheet(
            "QWidget{background:#11141b;color:#eef2ff;"
            "font-family:'Segoe UI',Tahoma;}"
            "QLabel#h{font-size:17px;font-weight:bold;}"
            "QLabel#d{color:#8b93a7;}"
            "QProgressBar{background:#1c2333;border:none;border-radius:8px;"
            "height:16px;text-align:center;color:white;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:8px;}"
            "QPushButton{background:#2563eb;border:none;border-radius:10px;"
            "padding:11px 28px;color:white;font-size:15px;font-weight:bold;}"
            "QPushButton:disabled{background:#1c2333;color:#565d6e;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        self._h = QLabel(tr("uninstall_q") if uninstall else tr("welcome"))
        self._h.setObjectName("h")
        self._d = QLabel("" if uninstall else tr("desc"))
        self._d.setObjectName("d")
        self._d.setWordWrap(True)
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.hide()
        self._btn = QPushButton(tr("yes") if uninstall else tr("install"))
        self._btn.clicked.connect(self._go)
        lay.addWidget(self._h)
        lay.addWidget(self._d)
        lay.addStretch(1)
        lay.addWidget(self._bar)
        lay.addWidget(self._btn, alignment=Qt.AlignLeft)

    def _go(self):
        self._btn.setEnabled(False)
        self._bar.show()
        self._h.setText(tr("uninstalling") if self._uninstall else tr("installing"))
        self._d.setText("")
        self._job = Job(self._uninstall)
        self._job.step.connect(lambda p, m: self._bar.setValue(p))
        self._job.done.connect(self._finished)
        self._job.start()

    def _finished(self, exe):
        self._app_exe = exe or None
        self._h.setText(tr("uninstalled") if self._uninstall else tr("done"))
        self._bar.setValue(100)
        self._btn.setEnabled(True)
        if self._uninstall:
            self._btn.setText(tr("close"))
            self._btn.clicked.disconnect()
            self._btn.clicked.connect(self.close)
        else:
            self._btn.setText(tr("launch"))
            self._btn.clicked.disconnect()
            self._btn.clicked.connect(self._launch)

    def _launch(self):
        if self._app_exe and os.path.exists(self._app_exe):
            os.startfile(self._app_exe)   # noqa: S606 - user-initiated
        self.close()


def run_gui(argv):
    uninstall = "--uninstall" in argv
    app = QApplication(argv)
    win = InstallerWindow(uninstall=uninstall)
    win.show()
    sys.exit(app.exec())
