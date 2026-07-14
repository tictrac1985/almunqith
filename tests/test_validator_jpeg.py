from almunqith.core.carve.validators.jpeg import validate_jpeg
from tests.helpers import make_jpeg


def test_clean_jpeg_is_complete_with_dimensions():
    data = make_jpeg(64, 48)
    r = validate_jpeg(data + b"\x00" * 100)   # trailing junk beyond EOI
    assert r.complete is True
    assert r.end == len(data)
    assert r.meta["width"] == 64 and r.meta["height"] == 48


def test_ff_fill_runs_between_segments_are_tolerated():
    data = make_jpeg()
    # inject 4 fill bytes before the second marker segment (after SOI)
    filled = data[:2] + b"\xff\xff\xff\xff" + data[2:]
    r = validate_jpeg(filled)
    assert r.complete is True
    assert r.end == len(filled)


def test_truncated_jpeg_is_incomplete():
    data = make_jpeg()
    r = validate_jpeg(data[: len(data) // 2])
    assert r.complete is False


def test_garbage_after_header_reports_break_offset():
    data = make_jpeg()
    corrupted = data[:20] + b"\x12\x34" + data[22:]
    r = validate_jpeg(corrupted)
    assert r.complete is False
    assert 0 < r.end <= 22
