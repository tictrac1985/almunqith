from almunqith.core.source import DiskImage
from almunqith.core.pipeline import Events, run_scan
from tests.helpers import make_jpeg


class Recorder(Events):
    def __init__(self):
        self.found = []
        self.logs = []
        self.progress = []

    def on_found(self, finding):
        self.found.append(finding)

    def on_log(self, key, **kw):
        self.logs.append((key, kw))

    def on_progress(self, done, total):
        self.progress.append((done, total))


def test_run_scan_emits_events_and_returns_findings(tmp_path):
    img = tmp_path / "t.img"
    img.write_bytes(b"\x00" * 512 + make_jpeg() + b"\x00" * 512)
    rec = Recorder()
    with DiskImage(img) as src:
        findings = run_scan(src, {"photos"}, rec, chunk_size=1024)
    assert len(findings) == 1 and findings[0].signature.name == "jpeg"
    assert rec.found == findings
    assert rec.logs[0][0] == "scan_started"
    assert rec.logs[-1] == ("scan_finished", {"found": 1})
    assert rec.progress[-1][0] == rec.progress[-1][1]
