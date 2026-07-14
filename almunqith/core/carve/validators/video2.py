"""Additional video validators: Matroska/WebM (EBML), ASF/WMV."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult

_EBML = b"\x1a\x45\xdf\xa3"
_ASF_HEADER_GUID = (b"\x30\x26\xb2\x75\x8e\x66\xcf\x11"
                    b"\xa6\xd9\x00\xaa\x00\x62\xce\x6c")


def _vint_size(first: int) -> int:
    mask = 0x80
    for length in range(1, 9):
        if first & mask:
            return length
        mask >>= 1
    return 0


def validate_mkv(data: bytes) -> ValidationResult:
    if data[:4] != _EBML:
        return ValidationResult(0, False, {})
    # find the Segment element (id 0x18538067) and read its size
    seg = data.find(b"\x18\x53\x80\x67")
    if seg == -1 or seg + 5 > len(data):
        return ValidationResult(len(data), False, {"kind": "mkv"})
    i = seg + 4
    size_len = _vint_size(data[i])
    if size_len == 0 or i + size_len > len(data):
        return ValidationResult(len(data), False, {"kind": "mkv"})
    raw = bytearray(data[i:i + size_len])
    raw[0] &= (0xFF >> size_len)
    size = int.from_bytes(raw, "big")
    # unknown-size segments (all bits set) stream to EOF
    if size >= (1 << (7 * size_len)) - 1:
        return ValidationResult(len(data), False, {"kind": "mkv"})
    end = i + size_len + size
    return ValidationResult(min(end, len(data)), end <= len(data),
                            {"kind": "mkv"})


def validate_asf(data: bytes) -> ValidationResult:
    if data[:16] != _ASF_HEADER_GUID:
        return ValidationResult(0, False, {})
    if len(data) < 30:
        return ValidationResult(len(data), False, {})
    # ASF Header Object size is a 64-bit LE at offset 16
    header_size = struct.unpack_from("<Q", data, 16)[0]
    if header_size < 30 or header_size > len(data):
        return ValidationResult(min(header_size, len(data)), False,
                                {"kind": "asf"})
    # the Data Object follows the header; its size is another 64-bit field
    if header_size + 24 > len(data):
        return ValidationResult(len(data), False, {"kind": "asf"})
    data_size = struct.unpack_from("<Q", data, header_size + 16)[0]
    end = header_size + data_size
    return ValidationResult(min(end, len(data)), end <= len(data),
                            {"kind": "asf"})
