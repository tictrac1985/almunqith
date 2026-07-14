"""RIFF container validator (AVI, WAV)."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult

_VARIANTS = {b"AVI ": "avi", b"WAVE": "wave"}


def validate_riff(data: bytes) -> ValidationResult:
    if len(data) < 12 or data[:4] != b"RIFF":
        return ValidationResult(0, False, {})
    variant = _VARIANTS.get(data[8:12])
    if variant is None:
        return ValidationResult(0, False, {})
    declared = struct.unpack_from("<I", data, 4)[0]
    end = 8 + declared
    meta = {"variant": variant}
    if declared < 4 or end > len(data):
        return ValidationResult(min(end, len(data)), False, meta)
    return ValidationResult(end, True, meta)
