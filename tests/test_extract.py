import os
import pytest
from almunqith.core.source import DiskImage
from almunqith.core.carve.signatures import for_categories
from almunqith.core.carve.scanner import scan
from almunqith.core.extract import extract
from tests.helpers import make_jpeg


def test_extract_saves_categorized_files_and_report(tmp_path):
    img = tmp_path / "t.img"
    j = make_jpeg()
    img.write_bytes(b"\x00" * 100 + j + b"\x00" * 50)
    dest = tmp_path / "out"
    with DiskImage(img) as src:
        findings = list(scan(src, for_categories({"photos"})))
        summary = extract(src, findings, str(dest))
    files = os.listdir(dest / "Photos")
    assert files == ["jpeg_00001.jpg"]
    assert (dest / "Photos" / "jpeg_00001.jpg").read_bytes() == j
    assert summary["saved"] == 1
    assert os.path.exists(summary["report_path"])
    assert "jpeg_00001.jpg" in (dest / "report.txt").read_text()


def test_extract_refuses_destination_on_source_drive(tmp_path):
    with pytest.raises(ValueError):
        extract(None, [], r"E:\out", source_drive="E:")
