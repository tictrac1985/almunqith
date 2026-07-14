"""Audio validators: MP3 (frame sync / ID3), FLAC, OGG, AAC-ADTS."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult

_MPEG_BITRATES = {
    # MPEG1 Layer III
    1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0],
}
_MPEG_RATES = [44100, 48000, 32000, 0]


def _mp3_frame_len(header: int):
    if (header & 0xFFE00000) != 0xFFE00000:
        return None
    layer = (header >> 17) & 3
    bitrate_idx = (header >> 12) & 0xF
    rate_idx = (header >> 10) & 3
    pad = (header >> 9) & 1
    if layer != 1 or bitrate_idx in (0, 15) or rate_idx == 3:
        return None
    bitrate = _MPEG_BITRATES[1][bitrate_idx] * 1000
    rate = _MPEG_RATES[rate_idx]
    if not bitrate or not rate:
        return None
    return int(144 * bitrate / rate) + pad


def validate_mp3(data: bytes) -> ValidationResult:
    start = 0
    meta = {}
    if data[:3] == b"ID3":
        if len(data) < 10:
            return ValidationResult(len(data), False, meta)
        size = 0
        for b in data[6:10]:
            size = (size << 7) | (b & 0x7F)
        start = 10 + size
        meta["id3"] = True
    if start + 4 > len(data) or data[start] != 0xFF:
        return ValidationResult(start if start else 0, False, meta)
    pos = start
    frames = 0
    while pos + 4 <= len(data):
        header = struct.unpack_from(">I", data, pos)[0]
        flen = _mp3_frame_len(header)
        if flen is None or flen < 4:
            break
        pos += flen
        frames += 1
    if frames < 2:
        return ValidationResult(start, False, meta)
    meta["frames"] = frames
    return ValidationResult(min(pos, len(data)), True, meta)


def validate_flac(data: bytes) -> ValidationResult:
    if data[:4] != b"fLaC":
        return ValidationResult(0, False, {})
    # walk metadata blocks; last flagged by high bit of block-type byte
    i = 4
    while i + 4 <= len(data):
        is_last = data[i] & 0x80
        size = struct.unpack_from(">I", b"\x00" + data[i + 1:i + 4])[0]
        i += 4 + size
        if is_last:
            break
    if i > len(data):
        return ValidationResult(len(data), False, {})
    return ValidationResult(min(i, len(data)), True, {})


def validate_ogg(data: bytes) -> ValidationResult:
    if data[:4] != b"OggS":
        return ValidationResult(0, False, {})
    last_end = 0
    i = 0
    guard = 0
    while i + 27 <= len(data) and data[i:i + 4] == b"OggS" and guard < 100000:
        nsegs = data[i + 26]
        if i + 27 + nsegs > len(data):
            break
        seg_table = data[i + 27:i + 27 + nsegs]
        body = sum(seg_table)
        i = i + 27 + nsegs + body
        last_end = i
        guard += 1
    if last_end == 0:
        return ValidationResult(len(data), False, {})
    return ValidationResult(min(last_end, len(data)), True, {})
