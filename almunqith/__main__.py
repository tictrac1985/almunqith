"""Entry point: `python -m almunqith` (or AlMunqith.exe) opens the wizard.

- Auto-elevates to administrator (raw-device reads need it) unless already
  elevated or running a self-test.
- Dev aid: ALMUNQITH_IMAGE=<path to .img> points the wizard at a disk image
  instead of a physical device (demo without admin / without a real card).
- ALMUNQITH_SELFTEST=1 constructs the UI offscreen and exits 0 (build check).
"""
import os
import sys


def _selftest() -> int:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtWidgets import QApplication
    from almunqith.ui.theme import DARK_QSS
    from almunqith.ui.wizard import Wizard
    app = QApplication([])
    app.setStyleSheet(DARK_QSS)
    win = Wizard()
    win.show()
    app.processEvents()
    return 0


def main():
    if os.environ.get("ALMUNQITH_SELFTEST") == "1":
        sys.exit(_selftest())

    # elevate unless we're only pointed at an image file (no raw device needed)
    if sys.platform == "win32" and not os.environ.get("ALMUNQITH_IMAGE"):
        from almunqith.ui.elevate import relaunch_as_admin
        if relaunch_as_admin():
            return          # elevated instance took over; this one exits

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from almunqith.ui.i18n import is_rtl
    from almunqith.ui.theme import DARK_QSS
    from almunqith.ui.wizard import Wizard

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    app.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)

    override = os.environ.get("ALMUNQITH_IMAGE")
    win = Wizard(source_override=override if override else None)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
