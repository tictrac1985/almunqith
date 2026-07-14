"""ISO-BMFF (MP4/MOV/3GP/HEIC container) box-walk validator."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult

_TOP_BOXES = {b"ftyp", b"moov", b"mdat", b"free", b"skip", b"wide",
              b"pdin", b"moof", b"mfra", b"meta", b"uuid", b"styp", b"sidx"}


def validate_mp4(data: bytes) -> ValidationResult:
    meta: dict = {}
    if len(data) < 12 or data[4:8] != b"ftyp":
        return ValidationResult(0, False, meta)
    meta["brand"] = data[8:12].decode("ascii", "replace")
    i = 0
    seen_media = False
    while i + 8 <= len(data):
        size = struct.unpack_from(">I", data, i)[0]
        name = data[i + 4:i + 8]
        if name not in _TOP_BOXES:
            return ValidationResult(i, seen_media and i > 0, meta)
        if size == 1:
            if i + 16 > len(data):
                return ValidationResult(len(data), False, meta)
            size = struct.unpack_from(">Q", data, i + 8)[0]
        elif size == 0:                       # box extends to end of file
            if name in (b"mdat", b"moov"):
                seen_media = True
            return ValidationResult(len(data), False, meta)
        if size < 8:
            return ValidationResult(i, False, meta)
        if name in (b"mdat", b"moov"):
            seen_media = True
        if i + size > len(data):
            return ValidationResult(len(data), False, meta)
        i += size
    return ValidationResult(i, seen_media, meta)
