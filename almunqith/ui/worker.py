"""Qt worker threads bridging the core engine to the UI."""
from PySide6.QtCore import QThread, Signal

from almunqith.core.pipeline import Events, run_scan
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
