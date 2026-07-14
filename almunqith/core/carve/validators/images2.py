"""Additional image validators: GIF, BMP, TIFF (and TIFF-based RAW)."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult


def validate_gif(data: bytes) -> ValidationResult:
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        return ValidationResult(0, False, {})
    if len(data) < 13:
        return ValidationResult(len(data), False, {})
    w, h = struct.unpack_from("<HH", data, 6)
    meta = {"width": w, "height": h}
    # GIF ends with trailer 0x3B; scan for it after the header (cheap heuristic
    # that still validates structure start + a plausible terminator)
    end = data.find(b"\x3b", 13)
    if end == -1:
        return ValidationResult(len(data), False, meta)
    return ValidationResult(end + 1, True, meta)


def validate_bmp(data: bytes) -> ValidationResult:
    if data[:2] != b"BM" or len(data) < 26:
        return ValidationResult(0, False, {})
    size = struct.unpack_from("<I", data, 2)[0]
    if size < 26 or size > len(data):
        return ValidationResult(min(size, len(data)), False, {})
    w, h = struct.unpack_from("<ii", data, 18)
    return ValidationResult(size, True, {"width": w, "height": abs(h)})


def _tiff(data: bytes):
    if data[:4] not in (b"II*\x00", b"MM\x00*"):
        return None
    le = data[:2] == b"II"
    return le


def validate_tiff(data: bytes) -> ValidationResult:
    le = _tiff(data)
    if le is None:
        return ValidationResult(0, False, {})
    end = 8
    try:
        ifd = struct.unpack_from("<I" if le else ">I", data, 4)[0]
        guard = 0
        while ifd and ifd + 2 <= len(data) and guard < 64:
            n = struct.unpack_from("<H" if le else ">H", data, ifd)[0]
            entry_end = ifd + 2 + n * 12
            if entry_end + 4 > len(data):
                return ValidationResult(len(data), False, {})
            end = max(end, entry_end + 4)
            ifd = struct.unpack_from("<I" if le else ">I", data, entry_end)[0]
            guard += 1
        return ValidationResult(min(end, len(data)), True, {})
    except struct.error:
        return ValidationResult(min(end, len(data)), False, {})
