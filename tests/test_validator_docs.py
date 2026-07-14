import io
import zipfile
import struct
from almunqith.core.carve.validators.docs import (
    validate_pdf, validate_zip, validate_ole2, validate_psd,
    validate_rar, validate_7z)


def test_pdf_complete():
    data = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
    r = validate_pdf(data + b"garbage")
    assert r.complete is True
    assert data[:r.end].endswith(b"%%EOF\n")


def test_zip_plain_and_docx_detection():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("hello.txt", "hi")
    data = buf.getvalue()
    r = validate_zip(data + b"tail")
    assert r.complete is True and r.meta["kind"] == "zip"

    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, "w") as z:
        z.writestr("[Content_Types].xml", "<x/>")
        z.writestr("word/document.xml", "<w/>")
    r2 = validate_zip(buf2.getvalue())
    assert r2.meta["kind"] == "docx"


def test_ole2_header():
    data = (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 22
            + struct.pack("<H", 9) + b"\x00" * 12
            + struct.pack("<I", 3) + b"\x00" * (512 - 48)
            + b"\x00" * (512 * 3))
    r = validate_ole2(data)
    assert r.complete is True and r.meta["kind"] == "ole2"


def test_psd_dims():
    data = b"8BPS" + b"\x00" * 10 + struct.pack(">II", 100, 200) + b"\x00" * 20
    r = validate_psd(data)
    assert r.complete is True and r.meta["width"] == 200


def test_rar_and_7z_detect():
    assert validate_rar(b"Rar!\x1a\x07\x00" + b"\x00" * 20).meta["kind"] == "rar"
    d7 = b"7z\xbc\xaf\x27\x1c" + b"\x00" * 4 + struct.pack("<QQ", 0, 0) + b"\x00" * 8
    assert validate_7z(d7).meta["kind"] == "7z"


def test_reject_foreign():
    assert validate_pdf(b"XXXX").end == 0
    assert validate_zip(b"XXXX").end == 0
    assert validate_ole2(b"XXXX").end == 0
