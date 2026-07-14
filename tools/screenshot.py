"""Render each wizard page to a PNG so we can eyeball the real UI headless."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

sys.path.insert(0, r"D:\AlMunqith")
from almunqith.ui.i18n import is_rtl  # noqa: E402
from almunqith.ui.theme import DARK_QSS  # noqa: E402
from almunqith.ui.wizard import Wizard  # noqa: E402
from almunqith.core.devices import DriveInfo  # noqa: E402

FAKE = [
    DriveInfo(1, r"\\.\PhysicalDrive1", 31_457_280_000, "USB",
              "Card Reader", ["E"], False),
    DriveInfo(2, r"\\.\PhysicalDrive2", 16_000_000_000, "USB",
              "USB Flash", ["F"], False),
    DriveInfo(0, r"\\.\PhysicalDrive0", 1_000_000_000_000, "NVMe",
              "Samsung SSD", ["C", "D"], True),
]

app = QApplication(sys.argv)
app.setStyleSheet(DARK_QSS)
app.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)

out = r"D:\AlMunqith\tools\shots"
os.makedirs(out, exist_ok=True)

w = Wizard(drives_provider=lambda: FAKE)
w.resize(880, 640)
w.show()
app.processEvents()

# page 1: drive selection
w.grab().save(os.path.join(out, "1_drive.png"))

# select + advance to types
w.drive_page.select_drive(FAKE[0])
app.processEvents()
w.go_next()
app.processEvents()
w.grab().save(os.path.join(out, "2_types.png"))

# advance to destination
w.go_next()
app.processEvents()
w.dest_page.set_path(r"D:\Recovered")
app.processEvents()
w.grab().save(os.path.join(out, "3_dest.png"))

# english variant of page 1
w._toggle_language()
app.processEvents()
while w.current_index() > 0:
    w.go_back()
app.processEvents()
w.grab().save(os.path.join(out, "4_drive_en.png"))

print("shots written to", out)
