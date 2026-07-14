"""PNG chunk-walk validator."""
import struct
import zlib

from almunqith.core.carve.validators.jpeg import ValidationResult

_SIG = b"\x89PNG\r\n\x1a\n"


def validate_png(data: bytes) -> ValidationResult:
    meta: dict = {}
    if not data.startswith(_SIG):
        return ValidationResult(0, False, meta)
    i = len(_SIG)
    first = True
    while i + 12 <= len(data):
        length = struct.unpack_from(">I", data, i)[0]
        ctype = data[i + 4:i + 8]
        if length > 0x7FFFFFFF or not ctype.isalpha():
            return ValidationResult(i, False, meta)
        end = i + 12 + length
        if end > len(data):
            return ValidationResult(len(data), False, meta)
        if first:
            if ctype != b"IHDR" or length != 13:
                return ValidationResult(i, False, meta)
            crc = struct.unpack_from(">I", data, i + 8 + length)[0]
            if zlib.crc32(data[i + 4:i + 8 + length]) & 0xFFFFFFFF != crc:
                return ValidationResult(i, False, meta)
            meta["width"], meta["height"] = struct.unpack_from(">II", data, i + 8)
            first = False
        if ctype == b"IEND":
            return ValidationResult(end, True, meta)
        i = end
    return ValidationResult(min(i, len(data)), False, meta)
