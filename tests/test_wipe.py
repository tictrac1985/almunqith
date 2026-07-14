import os
import pytest
from almunqith.core.wipe import (
    write_passes, assert_wipeable, SystemDiskError, format_script,
    PASSES_3, _pattern_block)
from almunqith.core.devices import DriveInfo


def test_write_passes_overwrites_file_with_final_random(tmp_path):
    p = tmp_path / "disk.bin"
    original = b"SECRET-DATA" * 1000
    p.write_bytes(original)
    size = p.stat().st_size
    seen = []
    with open(p, "r+b") as f:
        write_passes(f, size, ("zeros", "ones", "random"),
                     chunk=4096,
                     on_progress=lambda d, t, i, n: seen.append(n))
    data = p.read_bytes()
    assert original not in data                      # secret is gone
    assert len(data) == size                          # size preserved
    assert set(seen) == {"zeros", "ones", "random"}   # all passes ran


def test_zeros_then_ones_leave_expected_bytes(tmp_path):
    p = tmp_path / "d.bin"
    p.write_bytes(b"x" * 8192)
    with open(p, "r+b") as f:
        write_passes(f, 8192, ("zeros",), chunk=1024)
    assert p.read_bytes() == b"\x00" * 8192
    with open(p, "r+b") as f:
        write_passes(f, 8192, ("ones",), chunk=1024)
    assert p.read_bytes() == b"\xff" * 8192


def test_assert_wipeable_blocks_system_disk():
    sysdisk = DriveInfo(0, r"\\.\PhysicalDrive0", 1_000_000, "NVMe",
                        "SSD", ["C"], True)
    with pytest.raises(SystemDiskError):
        assert_wipeable(sysdisk)


def test_assert_wipeable_blocks_drive_with_c():
    d = DriveInfo(3, r"\\.\PhysicalDrive3", 1_000_000, "SATA",
                  "Disk", ["C", "E"], False)
    with pytest.raises(SystemDiskError):
        assert_wipeable(d)


def test_assert_wipeable_allows_removable():
    card = DriveInfo(1, r"\\.\PhysicalDrive1", 32_000_000_000, "USB",
                     "Card", ["E"], False)
    assert_wipeable(card)          # must not raise


def test_format_script_targets_disk_and_fs():
    s = format_script(2, fs="exFAT", label="CLEAN")
    assert "-Number 2" in s
    assert "-DiskNumber 2" in s
    assert "exFAT" in s and "CLEAN" in s
    assert "Format-Volume" in s


def test_pattern_block_values():
    assert _pattern_block("zeros", 4) == b"\x00\x00\x00\x00"
    assert _pattern_block("ones", 3) == b"\xff\xff\xff"
    assert len(_pattern_block("random", 16)) == 16
