import struct
from almunqith.core.carve.validators.riff import validate_riff
from almunqith.core.carve.validators.mp4 import validate_mp4


def _riff(variant=b"AVI ", payload=b"x" * 100):
    return b"RIFF" + struct.pack("<I", len(payload) + 4) + variant + payload


def _box(name: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + name + payload


def test_riff_avi_complete():
    data = _riff() + b"TRAILING"
    r = validate_riff(data)
    assert r.complete is True
    assert r.end == 8 + 104
    assert r.meta["variant"] == "avi"


def test_riff_declared_beyond_window_incomplete():
    data = b"RIFF" + struct.pack("<I", 10_000_000) + b"AVI " + b"x" * 50
    r = validate_riff(data)
    assert r.complete is False


def test_riff_wrong_fourcc_rejected():
    assert validate_riff(_riff(variant=b"XXXX")).end == 0


def test_mp4_box_chain_complete():
    data = (_box(b"ftyp", b"isom\x00\x00\x02\x00isomiso2")
            + _box(b"moov", b"m" * 40)
            + _box(b"mdat", b"d" * 200))
    r = validate_mp4(data)
    assert r.complete is True
    assert r.end == len(data)
    assert r.meta["brand"] == "isom"


def test_mp4_without_moov_or_mdat_incomplete():
    data = _box(b"ftyp", b"isom\x00\x00\x02\x00") + b"\x00" * 64
    r = validate_mp4(data)
    assert r.complete is False
