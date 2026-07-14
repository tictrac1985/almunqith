import struct
from almunqith.core.carve.validators.video2 import validate_mkv, validate_asf


def test_mkv_segment_sized():
    ebml_head = b"\x1a\x45\xdf\xa3" + b"\x84" + b"\x00" * 4   # 4-byte header
    body = b"B" * 50
    seg = b"\x18\x53\x80\x67" + bytes([0x80 | len(body)]) + body  # 1-byte size
    data = ebml_head + seg
    r = validate_mkv(data + b"tail")
    assert r.complete is True
    assert r.meta["kind"] == "mkv"


def test_asf_header_and_data():
    guid = (b"\x30\x26\xb2\x75\x8e\x66\xcf\x11"
            b"\xa6\xd9\x00\xaa\x00\x62\xce\x6c")
    header = guid + struct.pack("<Q", 30) + b"\x00" * 6
    data_obj = b"\x00" * 16 + struct.pack("<Q", 20) + b"\x00" * 12
    blob = header + data_obj
    r = validate_asf(blob)
    assert r.complete is True and r.meta["kind"] == "asf"


def test_reject_foreign():
    assert validate_mkv(b"XXXX").end == 0
    assert validate_asf(b"X" * 16).end == 0
