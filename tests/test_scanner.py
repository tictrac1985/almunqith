import os
import random
from almunqith.core.source import DiskImage
from almunqith.core.carve.signatures import for_categories
from almunqith.core.carve.scanner import scan
from tests.helpers import make_jpeg


def _build_image(tmp_path):
    rnd = random.Random(7)
    filler = bytes(rnd.randrange(256) for _ in range(64 * 1024))
    j1, j2 = make_jpeg(64, 48), make_jpeg(32, 32)
    layout = filler[:1000] + j1 + filler[:333] + j2 + filler
    p = tmp_path / "test.img"
    p.write_bytes(layout)
    return p, [(1000, len(j1)), (1000 + len(j1) + 333, len(j2))]


def test_scan_finds_jpegs_at_odd_offsets(tmp_path):
    p, expected = _build_image(tmp_path)
    with DiskImage(p) as src:
        found = [f for f in scan(src, for_categories({"photos"}))
                 if f.signature.name == "jpeg" and f.complete]
    assert [(f.offset, f.size) for f in found] == expected


def test_scan_reports_progress(tmp_path):
    p, _ = _build_image(tmp_path)
    ticks = []
    with DiskImage(p) as src:
        list(scan(src, for_categories({"photos"}),
                  chunk_size=32 * 1024,
                  on_progress=lambda done, total: ticks.append((done, total))))
    assert ticks and ticks[-1][0] == ticks[-1][1]
