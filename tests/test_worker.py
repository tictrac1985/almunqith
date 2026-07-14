from almunqith.ui.worker import ScanWorker, ExtractWorker
from tests.helpers import make_jpeg


def _image(tmp_path):
    p = tmp_path / "w.img"
    p.write_bytes(b"\x00" * 256 + make_jpeg() + b"\x00" * 256)
    return p


def test_scanworker_emits_and_finishes(qtbot, tmp_path):
    from almunqith.core.source import DiskImage
    p = _image(tmp_path)
    w = ScanWorker(lambda: DiskImage(p), {"photos"})
    results = {}
    w.finished_scan.connect(lambda f: results.setdefault("findings", f))
    with qtbot.waitSignal(w.finished_scan, timeout=10000):
        w.start()
    assert len(results["findings"]) == 1


def test_extractworker_saves(qtbot, tmp_path):
    from almunqith.core.source import DiskImage
    p = _image(tmp_path)
    w = ScanWorker(lambda: DiskImage(p), {"photos"})
    got = {}
    w.finished_scan.connect(lambda f: got.setdefault("f", f))
    with qtbot.waitSignal(w.finished_scan, timeout=10000):
        w.start()
    dest = tmp_path / "out"
    e = ExtractWorker(lambda: DiskImage(p), got["f"], str(dest))
    with qtbot.waitSignal(e.finished_extract, timeout=10000):
        e.start()
    assert (dest / "Photos" / "jpeg_00001.jpg").exists()
