"""NTFS undelete: scan MFT FILE records, recover deleted files' names,
sizes, timestamps and (for non-resident data) the first data-run offset.

Best-effort: handles resident $FILE_NAME and non-resident $DATA with a
first data run, the common layout for user files on NTFS.
"""
import struct
from datetime import datetime, timedelta, timezone

from almunqith.core.fs.common import RecoveredEntry

_FILE = b"FILE"
_ATTR_FILE_NAME = 0x30
_ATTR_DATA = 0x80
_END = 0xFFFFFFFF
# NTFS timestamps are 100-ns ticks since 1601-01-01
_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _filetime(ticks: int) -> str:
    if ticks <= 0:
        return ""
    try:
        dt = _EPOCH + timedelta(microseconds=ticks / 10)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (OverflowError, OSError):
        return ""


def _apply_fixup(rec: bytearray, sector_size: int):
    usa_off = struct.unpack_from("<H", rec, 4)[0]
    usa_cnt = struct.unpack_from("<H", rec, 6)[0]
    if usa_off == 0 or usa_cnt == 0:
        return
    usn = rec[usa_off:usa_off + 2]
    for i in range(1, usa_cnt):
        pos = i * sector_size - 2
        src = usa_off + i * 2
        if pos + 2 <= len(rec) and src + 2 <= len(rec):
            rec[pos:pos + 2] = rec[src:src + 2]


def _first_run_lcn(runs: bytes):
    """Decode the first data run; return (length_clusters, start_lcn) or None."""
    if not runs:
        return None
    header = runs[0]
    if header == 0:
        return None
    len_size = header & 0x0F
    off_size = (header >> 4) & 0x0F
    if len_size == 0 or 1 + len_size + off_size > len(runs):
        return None
    length = int.from_bytes(runs[1:1 + len_size], "little")
    off_bytes = runs[1 + len_size:1 + len_size + off_size]
    lcn = int.from_bytes(off_bytes, "little", signed=True)
    return length, lcn


def _parse_record(rec: bytearray, cluster_size: int, base_offset: int):
    if rec[:4] != _FILE:
        return None
    flags = struct.unpack_from("<H", rec, 22)[0]
    in_use = flags & 0x01
    if in_use:                       # only recover deleted records here
        return None
    attr_off = struct.unpack_from("<H", rec, 20)[0]
    name = ""
    mtime = ""
    size = 0
    data_offset = None
    i = attr_off
    guard = 0
    while i + 8 <= len(rec) and guard < 64:
        atype = struct.unpack_from("<I", rec, i)[0]
        if atype == _END:
            break
        alen = struct.unpack_from("<I", rec, i + 4)[0]
        if alen == 0 or i + alen > len(rec):
            break
        non_resident = rec[i + 8]
        if atype == _ATTR_FILE_NAME and not non_resident:
            coff = struct.unpack_from("<H", rec, i + 20)[0]
            c = i + coff
            if c + 66 <= len(rec):
                mtime_ticks = struct.unpack_from("<Q", rec, c + 24)[0]
                nlen = rec[c + 64]
                nm = rec[c + 66:c + 66 + nlen * 2]
                try:
                    decoded = nm.decode("utf-16-le")
                except UnicodeDecodeError:
                    decoded = ""
                # prefer a long name over 8.3; namespace byte at c+65 (2 == DOS)
                if decoded and (not name or rec[c + 65] != 2):
                    name = decoded
                    mtime = _filetime(mtime_ticks)
        elif atype == _ATTR_DATA:
            if non_resident:
                real_size = struct.unpack_from("<Q", rec, i + 48)[0]
                run_off = struct.unpack_from("<H", rec, i + 32)[0]
                run = _first_run_lcn(rec[i + run_off:i + alen])
                if run:
                    size = real_size
                    data_offset = base_offset + run[1] * cluster_size
            else:
                clen = struct.unpack_from("<I", rec, i + 16)[0]
                coff = struct.unpack_from("<H", rec, i + 20)[0]
                size = clen
                data_offset = base_offset + i + coff   # resident data in-record
        i += alen
        guard += 1

    if name and data_offset is not None and size > 0:
        return RecoveredEntry(name=name, size=size, first_offset=data_offset,
                              mtime=mtime, contiguous=True, fs="ntfs")
    return None


def scan_deleted(source, base_offset: int = 0, max_records: int = 100000):
    """Scan for NTFS MFT FILE records and recover deleted entries.

    Reads the boot sector for cluster size when present; scans forward for
    'FILE' records aligned to 1024 bytes. Returns a list of RecoveredEntry.
    """
    boot = source.read_at(base_offset, 512)
    cluster_size = 4096
    sector_size = 512
    if len(boot) >= 512 and boot[3:7] == b"NTFS":
        sector_size = struct.unpack_from("<H", boot, 11)[0] or 512
        spc = boot[13] or 8
        cluster_size = sector_size * spc

    results = []
    rec_size = 1024
    # scan the volume in windows looking for FILE records on 1024B boundaries
    CHUNK = 8 * 1024 * 1024
    pos = base_offset
    total = source.size
    scanned = 0
    while pos < total and scanned < max_records:
        buf = source.read_at(pos, CHUNK)
        if not buf:
            break
        for off in range(0, len(buf) - rec_size + 1, rec_size):
            if buf[off:off + 4] != _FILE:
                continue
            rec = bytearray(buf[off:off + rec_size])
            _apply_fixup(rec, sector_size)
            entry = _parse_record(rec, cluster_size, base_offset)
            if entry:
                results.append(entry)
            scanned += 1
            if scanned >= max_records:
                break
        pos += CHUNK
    return results
