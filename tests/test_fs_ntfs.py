import struct
from almunqith.core.source import DiskImage
from almunqith.core.fs.ntfs import scan_deleted, _filetime


def _build_ntfs_record(deleted=True, name="photo.jpg", size=2048,
                       lcn=10, cluster_size=4096):
    """Build a single 1024-byte MFT FILE record with $FILE_NAME + non-resident
    $DATA (no fixup application needed: we set USA count to 0)."""
    rec = bytearray(1024)
    rec[0:4] = b"FILE"
    struct.pack_into("<H", rec, 4, 0)      # USA offset 0 -> skip fixup
    struct.pack_into("<H", rec, 6, 0)      # USA count 0
    flags = 0x00 if deleted else 0x01
    struct.pack_into("<H", rec, 22, flags)
    attr_off = 56
    struct.pack_into("<H", rec, 20, attr_off)

    i = attr_off
    # ---- $FILE_NAME (resident) ----
    nm = name.encode("utf-16-le")
    content = bytearray(66 + len(nm))
    struct.pack_into("<Q", content, 24, 0)          # mtime ticks (0 -> "")
    content[64] = len(name)
    content[65] = 1                                  # namespace (long)
    content[66:66 + len(nm)] = nm
    clen = len(content)
    hdr = bytearray(24)
    struct.pack_into("<I", hdr, 0, 0x30)             # type $FILE_NAME
    attr_len = 24 + clen
    attr_len = (attr_len + 7) & ~7
    struct.pack_into("<I", hdr, 4, attr_len)
    hdr[8] = 0                                        # resident
    struct.pack_into("<I", hdr, 16, clen)            # content length
    struct.pack_into("<H", hdr, 20, 24)              # content offset
    rec[i:i + 24] = hdr
    rec[i + 24:i + 24 + clen] = content
    i += attr_len

    # ---- $DATA (non-resident) ----
    run = bytearray()
    run.append(0x14)                                 # len_size=4, off_size=1
    run += (1).to_bytes(4, "little")                 # 1 cluster
    run += (lcn).to_bytes(1, "little", signed=True)  # start LCN
    run.append(0x00)                                 # end of runs
    dhdr = bytearray(64)
    struct.pack_into("<I", dhdr, 0, 0x80)            # type $DATA
    run_off = 64
    dlen = run_off + len(run)
    dlen = (dlen + 7) & ~7
    struct.pack_into("<I", dhdr, 4, dlen)
    dhdr[8] = 1                                       # non-resident
    struct.pack_into("<H", dhdr, 32, run_off)        # data-run offset
    struct.pack_into("<Q", dhdr, 48, size)           # real size
    rec[i:i + 64] = dhdr
    rec[i + run_off:i + run_off + len(run)] = run
    i += dlen

    struct.pack_into("<I", rec, i, 0xFFFFFFFF)       # end marker
    return rec


def test_ntfs_recovers_deleted_file(tmp_path):
    cluster = 4096
    rec = _build_ntfs_record(deleted=True, name="photo.jpg", size=2048,
                             lcn=10, cluster_size=cluster)
    img = bytearray(1024 + rec.__len__() + 4096 * 12)
    # place record at a 1024 boundary (offset 1024)
    img[1024:1024 + 1024] = rec
    p = tmp_path / "ntfs.img"
    p.write_bytes(bytes(img))
    with DiskImage(p) as src:
        entries = scan_deleted(src)
    assert len(entries) == 1
    e = entries[0]
    assert e.name == "photo.jpg"
    assert e.size == 2048
    assert e.first_offset == 10 * cluster
    assert e.fs == "ntfs"


def test_ntfs_skips_in_use_records(tmp_path):
    rec = _build_ntfs_record(deleted=False)
    img = bytearray(2048 + 4096 * 12)
    img[1024:2048] = rec
    p = tmp_path / "ntfs2.img"
    p.write_bytes(bytes(img))
    with DiskImage(p) as src:
        assert scan_deleted(src) == []


def test_filetime_zero_empty():
    assert _filetime(0) == ""
