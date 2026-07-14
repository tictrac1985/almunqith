import struct
from almunqith.core.carve.validators.audio import (
    validate_mp3, validate_flac, validate_ogg)


def _mp3_frame():
    # MPEG1 Layer III, 128kbps, 44100Hz, no padding -> 417 bytes
    header = struct.pack(">I", 0xFFFB9000)
    return header + b"\x00" * (417 - 4)


def test_mp3_frame_run():
    data = _mp3_frame() * 4
    r = validate_mp3(data)
    assert r.complete is True and r.meta["frames"] >= 3


def test_mp3_with_id3():
    id3 = b"ID3\x03\x00\x00" + bytes([0, 0, 0, 10]) + b"\x00" * 10
    data = id3 + _mp3_frame() * 3
    r = validate_mp3(data)
    assert r.complete is True and r.meta.get("id3") is True


def test_flac_blocks():
    # one last metadata block of size 4, then no audio (structure still valid)
    block = b"\x80" + struct.pack(">I", 4)[1:] + b"\x00" * 4
    data = b"fLaC" + block
    r = validate_flac(data)
    assert r.complete is True


def test_ogg_pages():
    seg = b"\x02"
    page = b"OggS" + b"\x00" * 22 + b"\x01" + seg + b"\xff" * 2
    r = validate_ogg(page)
    assert r.complete is True


def test_reject_foreign():
    assert validate_mp3(b"XXXX").end == 0
    assert validate_flac(b"XXXX").end == 0
    assert validate_ogg(b"XXXX").end == 0
