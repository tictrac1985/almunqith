"""Fill-tolerant JPEG structure walker (ported from session rebuild tool)."""
import struct
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    end: int
    complete: bool
    meta: dict = field(default_factory=dict)


_KNOWN = (set(range(0xC0, 0xD0)) | {0xDA, 0xDB, 0xDD, 0xFE, 0x01}
          | set(range(0xE0, 0xF0)))


def validate_jpeg(data: bytes) -> ValidationResult:
    meta: dict = {}
    if data[:3] != b"\xff\xd8\xff":
        return ValidationResult(0, False, meta)
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            return ValidationResult(i, False, meta)
        while i + 1 < len(data) and data[i + 1] == 0xFF:   # legal fill bytes
            i += 1
        m = data[i + 1]
        if m == 0xD9:
            return ValidationResult(i + 2, True, meta)
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        if m not in _KNOWN:
            return ValidationResult(i, False, meta)
        seglen = struct.unpack_from(">H", data, i + 2)[0]
        if seglen < 2:
            return ValidationResult(i, False, meta)
        if m in (0xC0, 0xC1, 0xC2, 0xC3) and i + 9 < len(data):
            meta["height"] = struct.unpack_from(">H", data, i + 5)[0]
            meta["width"] = struct.unpack_from(">H", data, i + 7)[0]
        if m == 0xDA:
            j = i + 2 + seglen
            resumed = False
            while True:
                k = data.find(b"\xff", j)
                if k == -1 or k + 1 >= len(data):
                    return ValidationResult(len(data), False, meta)
                n = data[k + 1]
                if n == 0x00 or 0xD0 <= n <= 0xD7:
                    j = k + 2
                    continue
                if n == 0xFF:
                    j = k + 1
                    continue
                if n == 0xD9:
                    return ValidationResult(k + 2, True, meta)
                if n in _KNOWN:
                    i = k
                    resumed = True
                    break
                return ValidationResult(k, False, meta)
            if resumed:
                continue
        i += 2 + seglen
    return ValidationResult(i, False, meta)
