import io
import piexif
import pytest
from PIL import Image
from almunqith.core.rebuild.jpeg_salvage import salvage, parse_exif
from tests.helpers import make_jpeg


def test_salvage_plain_jpeg_has_no_thumbnail():
    thumb, meta = salvage(make_jpeg())
    assert thumb is None


def test_parse_exif_reads_make_model_when_present():
    # build a JPEG carrying EXIF make/model + a thumbnail via piexif
    piexif = pytest.importorskip("piexif")
    img = Image.new("RGB", (64, 48), (10, 20, 30))
    thumb_io = io.BytesIO()
    Image.new("RGB", (16, 12), (200, 100, 0)).save(thumb_io, "JPEG")
    exif = {
        "0th": {piexif.ImageIFD.Make: b"CANON",
                piexif.ImageIFD.Model: b"IXUS",
                piexif.ImageIFD.DateTime: b"2024:06:15 10:30:00"},
        "1st": {}, "Exif": {}, "GPS": {}, "Interop": {},
        "thumbnail": thumb_io.getvalue(),
    }
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=piexif.dump(exif))
    thumb, meta = salvage(buf.getvalue())
    assert meta.get("make") == "CANON"
    assert meta.get("model") == "IXUS"
    assert thumb is not None and thumb[:3] == b"\xff\xd8\xff"
