"""Document & archive validators: PDF, ZIP family (docx/xlsx/pptx), OLE2, RAR, 7z, PSD."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult


def validate_pdf(data: bytes) -> ValidationResult:
    if data[:5] != b"%PDF-":
        return ValidationResult(0, False, {})
    idx = data.rfind(b"%%EOF")
    if idx == -1:
        return ValidationResult(len(data), False, {})
    end = idx + 5
    # allow a trailing newline
    if end < len(data) and data[end:end + 1] in (b"\r", b"\n"):
        end += 1
    return ValidationResult(end, True, {})


_OOXML = {b"word/": "docx", b"xl/": "xlsx", b"ppt/": "pptx"}


def validate_zip(data: bytes) -> ValidationResult:
    if data[:4] != b"PK\x03\x04":
        return ValidationResult(0, False, {})
    eocd = data.rfind(b"PK\x05\x06")
    if eocd == -1 or eocd + 22 > len(data):
        return ValidationResult(len(data), False, {})
    comment_len = struct.unpack_from("<H", data, eocd + 20)[0]
    end = eocd + 22 + comment_len
    meta = {"kind": "zip"}
    head = data[:min(len(data), 4096)]
    for marker, kind in _OOXML.items():
        if marker in head:
            meta["kind"] = kind
            break
    return ValidationResult(min(end, len(data)), end <= len(data), meta)


def validate_ole2(data: bytes) -> ValidationResult:
    # Compound File Binary (legacy doc/xls/ppt/msi)
    if data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return ValidationResult(0, False, {})
    if len(data) < 512:
        return ValidationResult(len(data), False, {})
    sector_shift = struct.unpack_from("<H", data, 30)[0]
    if sector_shift not in (9, 12):
        return ValidationResult(0, False, {})
    num_sectors = struct.unpack_from("<I", data, 44)[0]
    sector = 1 << sector_shift
    end = 512 + num_sectors * sector
    # header + FAT sectors is a floor; the real file is at least this big
    return ValidationResult(min(end, len(data)),
                            end <= len(data) and end > 512, {"kind": "ole2"})


def validate_psd(data: bytes) -> ValidationResult:
    if data[:4] != b"8BPS":
        return ValidationResult(0, False, {})
    if len(data) < 26:
        return ValidationResult(len(data), False, {})
    h, w = struct.unpack_from(">II", data, 14)
    return ValidationResult(len(data), True, {"width": w, "height": h})


def validate_rar(data: bytes) -> ValidationResult:
    if data[:7] != b"Rar!\x1a\x07\x00" and data[:8] != b"Rar!\x1a\x07\x01\x00":
        return ValidationResult(0, False, {})
    return ValidationResult(len(data), False, {"kind": "rar"})


def validate_7z(data: bytes) -> ValidationResult:
    if data[:6] != b"7z\xbc\xaf\x27\x1c":
        return ValidationResult(0, False, {})
    if len(data) < 32:
        return ValidationResult(len(data), False, {})
    nh_off = struct.unpack_from("<Q", data, 12)[0]
    nh_size = struct.unpack_from("<Q", data, 20)[0]
    end = 32 + nh_off + nh_size
    return ValidationResult(min(end, len(data)), end <= len(data),
                            {"kind": "7z"})
