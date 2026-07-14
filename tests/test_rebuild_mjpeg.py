import io
import struct
from almunqith.core.source import DiskImage
from almunqith.core.rebuild.mjpeg_avi import build_avi, scan_frames, rebuild_videos
from almunqith.core.carve.validators.riff import validate_riff
from almunqith.core.carve.validators.jpeg import validate_jpeg
from tests.helpers import make_jpeg


def test_build_avi_is_valid_riff_with_frames():
    frames = [make_jpeg(64, 48) for _ in range(5)]
    out = io.BytesIO()
    n = build_avi(frames, out, 64, 48, fps=15.0)
    data = out.getvalue()
    assert n == 5
    # valid AVI container
    r = validate_riff(data)
    assert r.complete is True and r.meta["variant"] == "avi"
    # each 00dc chunk holds a decodable JPEG
    count = 0
    p = data.find(b"movi")
    idx = data.find(b"idx1")
    while True:
        p = data.find(b"00dc", p, idx)
        if p == -1:
            break
        size = struct.unpack_from("<I", data, p + 4)[0]
        frame = data[p + 8:p + 8 + size]
        assert validate_jpeg(frame).complete is True
        count += 1
        p += 4
    assert count == 5


def test_scan_and_rebuild_from_image(tmp_path):
    # lay 40 MJPEG frames contiguously in an image, then rebuild
    frames = [make_jpeg(80, 60) for _ in range(40)]
    blob = b"".join(frames)
    img = tmp_path / "vid.img"
    img.write_bytes(b"\x00" * 512 + blob + b"\x00" * 512)
    out_dir = tmp_path / "videos"
    with DiskImage(img) as src:
        found = list(scan_frames(src, 0, src.size))
        assert len(found) == 40
        videos = rebuild_videos(src, 0, src.size, str(out_dir), min_run=10)
    assert len(videos) == 1
    path, n = videos[0]
    assert n == 40
    # the rebuilt file is a valid AVI
    data = open(path, "rb").read()
    assert validate_riff(data).complete is True
