import os
from almunqith.core.source import DiskImage


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
