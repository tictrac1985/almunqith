import io
import struct
from PIL import Image
from almunqith.core.carve.validators.images2 import (
    validate_gif, validate_bmp, validate_tiff)


def _img(fmt, w=24, h=18):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (120, 60, 200)).save(buf, fmt)
    return buf.getvalue()


def test_gif_complete():
    data = _img("GIF")
    r = validate_gif(data + b"\x00\x00")
    assert r.complete is True
    assert r.meta["width"] == 24 and r.meta["height"] == 18


def test_bmp_complete_and_size():
    data = _img("BMP")
    r = validate_bmp(data + b"XYZ")
    assert r.complete is True
    assert r.end == len(data)
    assert r.meta["width"] == 24


def test_tiff_header_walk():
    data = _img("TIFF")
    r = validate_tiff(data)
    assert r.complete is True


def test_rejects_foreign_bytes():
    assert validate_gif(b"NOTAGIF").end == 0
    assert validate_bmp(b"XX").end == 0
    assert validate_tiff(b"____").end == 0
