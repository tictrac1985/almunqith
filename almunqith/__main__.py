"""Entry point: `python -m almunqith` opens the AlMunqith wizard.

Dev aid: set ALMUNQITH_IMAGE=<path to a .img> to point the wizard at a
disk image instead of a physical device (used to demo on the golden card
image without administrator rights).
"""
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from almunqith.ui.i18n import is_rtl
from almunqith.ui.theme import DARK_QSS
from almunqith.ui.wizard import Wizard


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    app.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)

    override = os.environ.get("ALMUNQITH_IMAGE")
    win = Wizard(source_override=override if override else None)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
