"""Filesystem pre-pass: detect the volume's filesystem and run the matching
undelete parser. Dispatching by the boot sector avoids, e.g., scanning an
entire 32 GB FAT card for NTFS MFT records.

Returns recovered named entries (with original names/dates). When the
filesystem can't be identified, returns [] and deep carve (level 2) takes over.
"""
from almunqith.core.fs import fat, ntfs
from almunqith.core.fs.common import RecoveredEntry


def detect_fs(source, base_offset: int = 0) -> str:
    boot = source.read_at(base_offset, 512)
    if len(boot) < 512:
        return "unknown"
    if boot[3:7] == b"NTFS":
        return "ntfs"
    # FAT: a valid BPB parse is the reliable signal (type strings are optional)
    if boot[510:512] == b"\x55\xaa" and fat._parse_bpb(boot) is not None:
        return "fat"
    return "unknown"


def scan_all(source, base_offset: int = 0) -> list:
    fs = detect_fs(source, base_offset)
    entries: list[RecoveredEntry] = []
    try:
        if fs == "ntfs":
            entries = ntfs.scan_deleted(source, base_offset)
        elif fs == "fat":
            entries = fat.scan_deleted(source, base_offset)
    except Exception:
        # a malformed volume must never abort recovery; deep carve follows
        entries = []
    return entries
