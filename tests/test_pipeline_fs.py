import os
from almunqith.core.source import DiskImage
from almunqith.core.pipeline import Events, run_scan
from almunqith.core.extract import extract
from tests.test_fs_fat import _build_fat16
from tests.helpers import make_jpeg


class Rec(Events):
    def __init__(self):
        self.logs = []

    def on_log(self, key, **kw):
        self.logs.append((key, kw))


def test_fs_prepass_yields_named_findings_and_extract_uses_name(tmp_path):
    # a FAT16 image whose deleted file "HOLIDAY.JPG" points at real JPEG bytes
    p, data_off = _build_fat16(tmp_path)
    # overwrite the data region with an actual JPEG so extraction is meaningful
    raw = bytearray(p.read_bytes())
    j = make_jpeg(48, 32)
    raw[data_off:data_off + len(j)] = j
    p.write_bytes(bytes(raw))

    rec = Rec()
    with DiskImage(p) as src:
        findings = run_scan(src, {"all"}, rec, chunk_size=4096)
        named = [f for f in findings if f.meta.get("name")]
        assert named, "FS pre-pass should yield at least one named finding"
        assert named[0].meta["name"] == "_OLIDAY.JPG"
        dest = tmp_path / "out"
        summary = extract(src, named, str(dest))

    assert ("fs_found", {"count": 1}) in rec.logs
    assert os.path.exists(dest / "Photos" / "_OLIDAY.JPG")
    assert summary["saved"] >= 1
