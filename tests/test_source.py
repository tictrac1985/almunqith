import os
from almunqith.core.source import DiskImage, RawDevice, SECTOR


def test_diskimage_reads_at_offset(tmp_path):
    p = tmp_path / "disk.img"
    p.write_bytes(b"A" * 100 + b"HELLO" + b"B" * 100)
    with DiskImage(p) as src:
        assert src.size == 205
        assert src.read_at(100, 5) == b"HELLO"
        assert src.read_at(0, 3) == b"AAA"


def test_diskimage_read_past_eof_returns_short(tmp_path):
    p = tmp_path / "disk.img"
    p.write_bytes(b"X" * 10)
    with DiskImage(p) as src:
        assert src.read_at(8, 100) == b"XX"
        assert src.read_at(500, 4) == b""


class FakeRaw(RawDevice):
    """RawDevice whose backing store is a bytes buffer (no real device)."""

    def __init__(self, data: bytes):
        self._data = data
        self.size = len(data)

    def _os_read(self, aligned_offset, aligned_length):
        assert aligned_offset % SECTOR == 0, "unaligned offset reached OS"
        assert aligned_length % SECTOR == 0, "unaligned length reached OS"
        return self._data[aligned_offset:aligned_offset + aligned_length]

    def close(self):
        pass


def test_rawdevice_unaligned_read_is_trimmed_correctly():
    data = bytes(range(256)) * 8  # 2048 bytes = 4 sectors
    dev = FakeRaw(data)
    assert dev.read_at(5, 10) == data[5:15]
    assert dev.read_at(510, 600) == data[510:1110]
    assert dev.read_at(0, 512) == data[:512]


def test_rawdevice_read_clamped_to_size():
    data = b"Z" * 1024
    dev = FakeRaw(data)
    assert dev.read_at(1000, 500) == data[1000:]
