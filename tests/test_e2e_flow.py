from almunqith.ui.wizard import Wizard
from almunqith.core.devices import DriveInfo
from tests.helpers import make_jpeg


FAKE = [DriveInfo(1, r"\\.\PhysicalDrive1", 31_457_280_000, "USB",
                  "Card Reader", ["E"], False)]


def test_full_journey_on_image(qtbot, tmp_path):
    img = tmp_path / "card.img"
    img.write_bytes(b"\x00" * 500 + make_jpeg(80, 60) + b"\x00" * 500)
    dest = tmp_path / "recovered"

    w = Wizard(drives_provider=lambda: FAKE, source_override=str(img))
    qtbot.addWidget(w)

    # step 1: pick drive
    w.drive_page.select_drive(FAKE[0])
    w.go_next()
    assert w.current_index() == 1

    # step 2: photos
    w.types_page._buttons["all"].setChecked(False)
    w.types_page._buttons["photos"].setChecked(True)
    w.types_page.selection_changed.emit()
    w.go_next()
    assert w.current_index() == 2

    # step 3: destination
    w.dest_page.set_path(str(dest))
    w.go_next()
    assert w.current_index() == 3          # scan page, auto-starts

    # step 4 -> 5: wait for scan to finish and auto-advance to results
    with qtbot.waitSignal(w.scan_page.scan_done, timeout=15000):
        pass
    assert w.current_index() == 4
    assert len(w.results_page.selected_findings()) == 1

    # extract
    with qtbot.waitSignal(w.results_page.extract_done, timeout=15000):
        w.results_page.extract_to(str(dest), w._source_factory())
    assert (dest / "Photos" / "jpeg_00001.jpg").exists()
    assert (dest / "report.txt").exists()
