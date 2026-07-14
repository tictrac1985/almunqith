from almunqith.ui.wizard import Wizard
from almunqith.core.devices import DriveInfo


FAKE = [DriveInfo(1, r"\\.\PhysicalDrive1", 31_457_280_000, "USB",
                  "Card Reader", ["E"], False)]


def test_wizard_has_five_pages_and_bounded_nav(qtbot):
    w = Wizard(drives_provider=lambda: FAKE)
    qtbot.addWidget(w)
    assert w.pages.count() == 5
    assert w.current_index() == 0
    w.go_back()
    assert w.current_index() == 0          # bounded at start


def test_wizard_next_requires_page_readiness(qtbot):
    w = Wizard(drives_provider=lambda: FAKE)
    qtbot.addWidget(w)
    w.go_next()                            # no drive selected yet
    assert w.current_index() == 0
    w.drive_page.select_drive(FAKE[0])
    w.go_next()
    assert w.current_index() == 1
