import os
import pytest
from almunqith.core.source import DiskImage
from almunqith.core.pipeline import Events, run_scan

GOLDEN = r"D:\Recovery\card.img"


@pytest.mark.skipif(not os.path.exists(GOLDEN),
                    reason="golden card image not present")
def test_engine_finds_real_camera_jpegs_in_golden_image():
    class Count(Events):
        found = 0

        def on_found(self, f):
            if f.signature.name == "jpeg" and f.complete:
                Count.found += 1

    with DiskImage(GOLDEN) as src:
        # first 256 MiB of the real card contains thousands of MJPEG frames
        src.size = 256 * 1024 * 1024
        run_scan(src, {"photos"}, Count())
    assert Count.found > 1000
