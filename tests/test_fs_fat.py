import struct
from almunqith.core.source import DiskImage
from almunqith.core.fs.fat import scan_deleted, _dos_datetime


def _build_fat16(tmp_path):
    """Minimal FAT16 volume: 512B sectors, 1 sector/cluster, 1 FAT,
    16 root entries, with one deleted file entry pointing at cluster 2."""
    bps = 512
    spc = 1
    reserved = 1
    num_fats = 1
    root_entries = 16
    fatsz = 1
    total = 64

    boot = bytearray(bps)
    struct.pack_into("<H", boot, 11, bps)
    boot[13] = spc
    struct.pack_into("<H", boot, 14, reserved)
    boot[16] = num_fats
    struct.pack_into("<H", boot, 17, root_entries)
    struct.pack_into("<H", boot, 19, total)
    struct.pack_into("<H", boot, 22, fatsz)
    boot[510], boot[511] = 0x55, 0xAA

    fat = bytearray(fatsz * bps)

    root = bytearray(root_entries * 32)
    # deleted file "HOLIDAY.JPG", size 1000, first cluster 2, date 2024-06-15 10:30:00
    e = bytearray(32)
    e[0] = 0xE5
    e[1:8] = b"OLIDAY "          # first char replaced by 0xE5
    e[8:11] = b"JPG"
    e[11] = 0x20                  # archive attr
    wdate = ((2024 - 1980) << 9) | (6 << 5) | 15
    wtime = (10 << 11) | (30 << 5) | (0 // 2)
    struct.pack_into("<H", e, 22, wtime)
    struct.pack_into("<H", e, 24, wdate)
    struct.pack_into("<H", e, 26, 2)          # low cluster word
    struct.pack_into("<H", e, 20, 0)          # high cluster word
    struct.pack_into("<I", e, 28, 1000)       # size
    root[0:32] = e

    # data region: cluster 2 holds recognizable bytes
    root_dir_sectors = (root_entries * 32) // bps
    first_data_sector = reserved + num_fats * fatsz + root_dir_sectors
    img = bytearray(first_data_sector * bps + spc * bps * 4)
    img[0:bps] = boot
    fat_start = reserved * bps
    img[fat_start:fat_start + len(fat)] = fat
    root_start = (reserved + num_fats * fatsz) * bps
    img[root_start:root_start + len(root)] = root
    data_off = first_data_sector * bps
    img[data_off:data_off + 8] = b"JPEGDATA"

    p = tmp_path / "fat16.img"
    p.write_bytes(img)
    return p, data_off


def test_fat_recovers_deleted_entry(tmp_path):
    p, data_off = _build_fat16(tmp_path)
    with DiskImage(p) as src:
        entries = scan_deleted(src)
    assert len(entries) == 1
    e = entries[0]
    assert e.name == "_OLIDAY.JPG"
    assert e.size == 1000
    assert e.first_offset == data_off
    assert e.mtime == "2024-06-15 10:30:00"
    assert e.fs == "fat"


def test_dos_datetime_zero_is_empty():
    assert _dos_datetime(0, 0) == ""


def test_non_fat_source_returns_empty(tmp_path):
    p = tmp_path / "junk.img"
    p.write_bytes(b"\x00" * 4096)
    with DiskImage(p) as src:
        assert scan_deleted(src) == []
