"""Salvage data from corrupted JPEGs: extract the embedded EXIF thumbnail
(stored in the first ~64 KB and often intact when the main image is damaged)
and the camera make/model/date. Ported from the session salvage tool.
"""
import struct


def _u16(b, o, le):
    return struct.unpack_from("<H" if le else ">H", b, o)[0]


def _u32(b, o, le):
    return struct.unpack_from("<I" if le else ">I", b, o)[0]


def parse_exif(data: bytes):
    """Return dict with optional keys make, model, datetime, thumbnail(bytes)."""
    result = {}
    if data[:2] != b"\xff\xd8":
        return result
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        if marker == 0xD8:
            i += 2
            continue
        if marker in (0xD9, 0xDA):
            break
        seglen = struct.unpack_from(">H", data, i + 2)[0]
        if seglen < 2:
            break
        if marker == 0xE1 and data[i + 4:i + 10] == b"Exif\x00\x00":
            _parse_tiff(data, i + 10, result)
            break
        i += 2 + seglen
    return result


def _parse_tiff(data, tiff, result):
    try:
        le = data[tiff:tiff + 2] == b"II"

        def read_ifd(off):
            tags = {}
            n = _u16(data, off, le)
            if n > 200:
                raise ValueError
            for k in range(n):
                e = off + 2 + 12 * k
                tag = _u16(data, e, le)
                tags[tag] = e + 8
            nxt = _u32(data, off + 2 + 12 * n, le)
            return tags, nxt

        def ascii_at(pos, count):
            off = (_u32(data, pos, le) + tiff) if count > 4 else pos
            return data[off:off + count].split(b"\x00")[0].decode(
                "ascii", "replace").strip()

        ifd0 = tiff + _u32(data, tiff + 4, le)
        tags0, ifd1_off = read_ifd(ifd0)
        if 0x010F in tags0:
            result["make"] = ascii_at(tags0[0x010F],
                                      _u32(data, tags0[0x010F] - 4, le))
        if 0x0110 in tags0:
            result["model"] = ascii_at(tags0[0x0110],
                                       _u32(data, tags0[0x0110] - 4, le))
        if 0x0132 in tags0:
            result["datetime"] = ascii_at(tags0[0x0132], 20)
        if ifd1_off:
            tags1, _ = read_ifd(tiff + ifd1_off)
            if 0x0201 in tags1 and 0x0202 in tags1:
                to = _u32(data, tags1[0x0201], le) + tiff
                tl = _u32(data, tags1[0x0202], le)
                if 0 < tl < 512 * 1024 and to + tl <= len(data):
                    tb = data[to:to + tl]
                    if tb[:3] == b"\xff\xd8\xff":
                        result["thumbnail"] = tb
    except (struct.error, ValueError, UnicodeDecodeError):
        pass


def salvage(data: bytes):
    """Return (thumbnail_bytes_or_None, metadata_dict)."""
    meta = parse_exif(data)
    thumb = meta.pop("thumbnail", None)
    return thumb, meta
