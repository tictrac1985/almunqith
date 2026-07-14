"""Qt worker threads bridging the core engine to the UI."""
from PySide6.QtCore import QThread, Signal

from almunqith.core.pipeline import Events, run_scan, rebuild_fragmented_videos
from almunqith.core.extract import extract


class _Relay(Events):
    def __init__(self, worker):
        self.w = worker

    def on_progress(self, done, total):
        self.w.progress.emit(done, total)

    def on_found(self, finding):
        self.w.found.emit(finding)

    def on_log(self, key, **kw):
        self.w.log.emit(key, kw)


class ScanWorker(QThread):
    progress = Signal(int, int)
    found = Signal(object)
    log = Signal(str, dict)
    finished_scan = Signal(list)

    def __init__(self, source_factory, categories):
        super().__init__()
        self._factory = source_factory
        self._categories = categories

    def run(self):
        source = self._factory()
        try:
            findings = run_scan(source, self._categories, _Relay(self))
        finally:
            close = getattr(source, "close", None)
            if close:
                close()
        self.finished_scan.emit(findings)


class ExtractWorker(QThread):
    saved = Signal(int, int)
    finished_extract = Signal(dict)

    def __init__(self, source_factory, findings, dest_dir, source_drive=None):
        super().__init__()
        self._factory = source_factory
        self._findings = findings
        self._dest = dest_dir
        self._drive = source_drive

    def run(self):
        source = self._factory()
        try:
            summary = extract(source, self._findings, self._dest,
                              on_saved=lambda a, b: self.saved.emit(a, b),
                              source_drive=self._drive)
        finally:
            close = getattr(source, "close", None)
            if close:
                close()
        self.finished_extract.emit(summary)


class _LogRelay(Events):
    def __init__(self, worker):
        self.w = worker

    def on_log(self, key, **kw):
        self.w.log.emit(key, kw)


class RebuildWorker(QThread):
    """Level-4 processor thread: rebuild fragmented MJPEG videos."""
    log = Signal(str, dict)
    finished_rebuild = Signal(list)

    def __init__(self, source_factory, out_dir):
        super().__init__()
        self._factory = source_factory
        self._out = out_dir

    def run(self):
        source = self._factory()
        try:
            videos = rebuild_fragmented_videos(source, self._out,
                                               _LogRelay(self))
        finally:
            close = getattr(source, "close", None)
            if close:
                close()
        self.finished_rebuild.emit(videos)


class WipeWorker(QThread):
    """Secure-wipe thread (destructive). Runs the multi-pass overwrite +
    format on a real device. The wipe function is injectable for testing."""
    progress = Signal(int, int, int, str)     # done, total, pass_idx, name
    log = Signal(str, dict)
    finished_wipe = Signal(dict)

    def __init__(self, drive_info, passes, wipe_func=None):
        super().__init__()
        self._drive = drive_info
        self._passes = passes
        if wipe_func is None:
            from almunqith.core.wipe import secure_wipe
            wipe_func = secure_wipe
        self._wipe = wipe_func

    def run(self):
        summary = self._wipe(
            self._drive, passes=self._passes,
            on_progress=lambda d, t, i, n: self.progress.emit(d, t, i, n),
            on_log=lambda k, **kw: self.log.emit(k, kw))
        self.finished_wipe.emit(summary or {"ok": True})
