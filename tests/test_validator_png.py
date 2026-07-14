import io
from PIL import Image
from almunqith.core.carve.validators.png import validate_png


def _make_png(w=32, h=16) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (10, 200, 50)).save(buf, "PNG")
    return buf.getvalue()


def test_clean_png_complete_with_dimensions():
    data = _make_png(32, 16)
    r = validate_png(data + b"JUNKJUNK")
    assert r.complete is True
    assert r.end == len(data)
    assert r.meta == {"width": 32, "height": 16}


def test_truncated_png_incomplete():
    data = _make_png()
    r = validate_png(data[:40])
    assert r.complete is False


def test_corrupted_ihdr_crc_rejected():
    data = bytearray(_make_png())
    data[20] ^= 0xFF                     # flip a byte inside IHDR data
    r = validate_png(bytes(data))
    assert r.complete is False
