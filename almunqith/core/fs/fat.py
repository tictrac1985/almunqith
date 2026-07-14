"""FAT12/16/32 undelete: recover deleted directory entries (0xE5) with names,
sizes, dates and starting cluster. Assumes contiguous data (best effort for
the common camera/flash case where the FAT chain for a deleted file is gone).
"""
import struct

from almunqith.core.fs.common import RecoveredEntry

_ATTR_LFN = 0x0F
_ATTR_DIR = 0x10
_ATTR_VOLUME = 0x08


def _dos_datetime(date_w: int, time_w: int) -> str:
    if date_w == 0:
        return ""
    day = date_w & 0x1F
    month = (date_w >> 5) & 0x0F
    year = 1980 + ((date_w >> 9) & 0x7F)
    sec = (time_w & 0x1F) * 2
    minute = (time_w >> 5) & 0x3F
    hour = (time_w >> 11) & 0x1F
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return ""
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{sec:02d}"


def _parse_bpb(boot: bytes):
    if len(boot) < 512 or boot[510:512] != b"\x55\xaa":
        return None
    bytes_per_sec = struct.unpack_from("<H", boot, 11)[0]
    sec_per_clus = boot[13]
    reserved = struct.unpack_from("<H", boot, 14)[0]
    num_fats = boot[16]
    root_entries = struct.unpack_from("<H", boot, 17)[0]
    total16 = struct.unpack_from("<H", boot, 19)[0]
    fatsz16 = struct.unpack_from("<H", boot, 22)[0]
    total32 = struct.unpack_from("<I", boot, 32)[0]
    fatsz32 = struct.unpack_from("<I", boot, 36)[0]
    root_clus = struct.unpack_from("<I", boot, 44)[0]
    if bytes_per_sec not in (512, 1024, 2048, 4096) or sec_per_clus == 0:
        return None
    fatsz = fatsz16 or fatsz32
    total = total16 or total32
    if fatsz == 0 or total == 0:
        return None
    root_dir_sectors = ((root_entries * 32) + (bytes_per_sec - 1)) // bytes_per_sec
    first_data_sector = reserved + num_fats * fatsz + root_dir_sectors
    is_fat32 = root_entries == 0
    return {
        "bps": bytes_per_sec, "spc": sec_per_clus, "reserved": reserved,
        "num_fats": num_fats, "fatsz": fatsz, "root_entries": root_entries,
        "root_dir_sectors": root_dir_sectors, "first_data_sector": first_data_sector,
        "is_fat32": is_fat32, "root_clus": root_clus,
    }


def _cluster_offset(bpb, cluster: int) -> int:
    first = bpb["first_data_sector"] + (cluster - 2) * bpb["spc"]
    return first * bpb["bps"]


def _decode_lfn(entries) -> str:
    """entries: list of 32-byte LFN slots in on-disk order (reversed sequence)."""
    parts = {}
    for e in entries:
        seq = e[0] & 0x3F
        chars = e[1:11] + e[14:26] + e[28:32]
        parts[seq] = chars
    out = b""
    for seq in sorted(parts):
        out += parts[seq]
    try:
        name = out.decode("utf-16-le")
    except UnicodeDecodeError:
        return ""
    return name.split("\x00")[0]


def _iter_dir(data: bytes, base_offset: int, bpb):
    """Yield RecoveredEntry for deleted files found in a directory byte block."""
    lfn_stack = []
    for i in range(0, len(data) - 32 + 1, 32):
        e = data[i:i + 32]
        first = e[0]
        if first == 0x00:
            lfn_stack = []
            continue
        attr = e[11]
        if attr == _ATTR_LFN:
            lfn_stack.append(e)
            continue
        if attr & (_ATTR_VOLUME | _ATTR_DIR):
            lfn_stack = []
            continue
        if first == 0xE5:                     # deleted entry
            size = struct.unpack_from("<I", e, 28)[0]
            hi = struct.unpack_from("<H", e, 20)[0]
            lo = struct.unpack_from("<H", e, 26)[0]
            cluster = (hi << 16) | lo
            wtime = struct.unpack_from("<H", e, 22)[0]
            wdate = struct.unpack_from("<H", e, 24)[0]
            name = ""
            if lfn_stack:
                name = _decode_lfn(lfn_stack)
            if not name:
                base = e[1:8].decode("ascii", "replace").strip()
                ext = e[8:11].decode("ascii", "replace").strip()
                name = f"_{base}.{ext}" if ext else f"_{base}"
            if cluster >= 2 and 0 < size < 4 * 1024 ** 3:
                yield RecoveredEntry(
                    name=name, size=size,
                    first_offset=base_offset + _cluster_offset(bpb, cluster),
                    mtime=_dos_datetime(wdate, wtime),
                    contiguous=True, fs="fat")
        lfn_stack = []


def scan_deleted(source, base_offset: int = 0):
    """Scan a FAT volume (starting at base_offset) for deleted files.

    Reads the root directory and (for FAT32) does a shallow walk. Returns a
    list of RecoveredEntry. Non-FAT sources yield an empty list.
    """
    boot = source.read_at(base_offset, 512)
    bpb = _parse_bpb(boot)
    if bpb is None:
        return []
    results = []
    bps = bpb["bps"]
    if bpb["is_fat32"]:
        # root is a normal cluster chain; read a bounded span from root cluster
        root_off = base_offset + _cluster_offset(bpb, bpb["root_clus"])
        span = source.read_at(root_off, bpb["spc"] * bps * 32)
        results += list(_iter_dir(span, base_offset, bpb))
    else:
        root_start = (bpb["reserved"] + bpb["num_fats"] * bpb["fatsz"]) * bps
        span = source.read_at(base_offset + root_start,
                              bpb["root_entries"] * 32)
        results += list(_iter_dir(span, base_offset, bpb))
    return results
