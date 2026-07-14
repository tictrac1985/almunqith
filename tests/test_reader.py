import threading
from almunqith.core.reader import ResilientReader, Gap


class GoodSource:
    size = 4096

    def read_at(self, offset, length):
        return b"G" * length


class HangingSource:
    """Blocks forever on a chosen offset, normal elsewhere."""
    size = 4096

    def __init__(self, hang_offset):
        self.hang_offset = hang_offset
        self.release = threading.Event()

    def read_at(self, offset, length):
        if offset == self.hang_offset:
            self.release.wait(10)
        return b"H" * length


def test_normal_reads_pass_through():
    r = ResilientReader(GoodSource(), timeout_s=1.0)
    assert r.read_at(0, 100) == b"G" * 100
    assert r.gaps == []


def test_hang_then_reopen_recovers():
    events = []
    reopened = GoodSource()
    r = ResilientReader(HangingSource(hang_offset=512), timeout_s=0.2,
                        reopen=lambda: reopened,
                        on_event=lambda k, d: events.append(k))
    assert r.read_at(512, 64) == b"G" * 64      # retried on fresh source
    assert "read_timeout" in events and "reopened" in events
    assert r.gaps == []


def test_hang_without_reopen_records_gap():
    r = ResilientReader(HangingSource(hang_offset=0), timeout_s=0.2)
    assert r.read_at(0, 64) is None
    assert r.gaps == [Gap(start=0, end=64, reason="hang")]
