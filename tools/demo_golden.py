"""Drive the real wizard against the golden card image, headless, and prove
it recovers real files end-to-end through the actual UI code path."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402

sys.path.insert(0, r"D:\AlMunqith")
from almunqith.ui.wizard import Wizard  # noqa: E402
from almunqith.core.devices import DriveInfo  # noqa: E402

GOLDEN = r"D:\Recovery\card.img"
DEST = r"D:\AlMunqith\tools\demo_out"

FAKE = [DriveInfo(1, r"\\.\PhysicalDrive1", 31_457_280_000, "USB",
                  "Card Reader", ["E"], False)]

app = QApplication(sys.argv)
w = Wizard(drives_provider=lambda: FAKE, source_override=GOLDEN)

w.drive_page.select_drive(FAKE[0])
w.go_next()                       # -> types
w.types_page._buttons["all"].setChecked(False)
w.types_page._buttons["photos"].setChecked(True)
w.types_page.selection_changed.emit()
w.go_next()                       # -> dest
w.dest_page.set_path(DEST)
w.go_next()                       # -> scan (auto-starts)

done = {"n": 0}
w.scan_page.scan_done.connect(lambda f: done.update(n=len(f)))
# pump the event loop until the scan thread finishes
w.scan_page._worker.wait(600000)
app.processEvents()

print(f"scan found {done['n']} findings via the real UI pipeline")
saved = {"s": None}
w.results_page.extract_done.connect(lambda s: saved.update(s=s))
# limit extraction to first 30 to keep the demo quick
w.results_page._lists  # ensure loaded
findings = w.results_page.selected_findings()[:30]
from almunqith.core.extract import extract  # noqa: E402
from almunqith.core.source import DiskImage  # noqa: E402
src = DiskImage(GOLDEN)
summary = extract(src, findings, DEST)
src.close()
print(f"extracted {summary['saved']} files to {DEST}")
