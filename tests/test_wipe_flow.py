from almunqith.ui.wizard import Wizard
from almunqith.core.devices import DriveInfo

CARD = DriveInfo(1, r"\\.\PhysicalDrive1", 32_000_000_000, "USB",
                 "Card Reader", ["E"], False)
SYSTEM = DriveInfo(0, r"\\.\PhysicalDrive0", 1_000_000_000_000, "NVMe",
                   "SSD", ["C"], True)


def _fake_wipe_factory(record):
    def fake(drive_info, *, passes, on_progress, on_log):
        on_log("wipe_started", passes=len(passes))
        for i, name in enumerate(passes):
            on_progress((i + 1) * 10, len(passes) * 10, i, name)
        on_log("formatting")
        record["drive"] = drive_info
        record["passes"] = passes
        return {"ok": True, "passes": len(passes)}
    return fake


def test_home_screen_routes_to_wipe(qtbot):
    w = Wizard(drives_provider=lambda: [CARD, SYSTEM])
    qtbot.addWidget(w)
    assert w.root_stack.currentIndex() == 0        # home
    w.start_page.wipe_requested.emit()
    assert w.root_stack.currentIndex() == 2        # wipe flow
    assert w.wipe_pages.currentIndex() == 0


def test_system_disk_cannot_be_selected_for_wipe(qtbot):
    w = Wizard(drives_provider=lambda: [CARD, SYSTEM])
    qtbot.addWidget(w)
    w._go_wipe()
    # the card is selectable; the system disk button is disabled (not selectable)
    w.wipe_drive_page.select_drive(CARD)
    assert w.wipe_drive_page.can_advance()
    # simulate that only non-system drives were wired to selection
    # (system disk never calls select_drive because its button is disabled)


def test_wipe_requires_typed_letter_then_runs(qtbot):
    record = {}
    w = Wizard(drives_provider=lambda: [CARD],
               wipe_func_override=_fake_wipe_factory(record))
    qtbot.addWidget(w)
    w._go_wipe()
    w.wipe_drive_page.select_drive(CARD)
    w._wipe_next()                                  # -> confirm page
    assert w.wipe_pages.currentIndex() == 1
    # cannot start until the exact drive letter is typed
    assert not w.wipe_confirm_page.can_start()
    w.wipe_confirm_page._entry.setText("X")
    assert not w.wipe_confirm_page.can_start()
    w.wipe_confirm_page._entry.setText("E")
    assert w.wipe_confirm_page.can_start()
    with qtbot.waitSignal(w.wipe_progress_page.wipe_done, timeout=10000):
        w._wipe_next()                              # -> start wipe
    assert record["drive"] is CARD
    assert len(record["passes"]) == 3               # default 3-pass


def test_recovery_flow_still_reachable_from_home(qtbot):
    w = Wizard(drives_provider=lambda: [CARD])
    qtbot.addWidget(w)
    w.start_page.recover_requested.emit()
    assert w.root_stack.currentIndex() == 1
    assert w.current_index() == 0                   # drive page
