"""Recovery pipeline: M1 exposes the deep-carve level; the escalation
ladder from the spec (quick look, FS undelete, rescue imaging, rebuild
processors) bolts onto run_scan in M3/M4."""
from almunqith.core.carve.scanner import scan
from almunqith.core.carve.signatures import for_categories


class Events:
    def on_progress(self, done: int, total: int):
        pass

    def on_found(self, finding):
        pass

    def on_log(self, key: str, **kw):
        pass


def run_scan(source, categories: set, events: Events,
             *, chunk_size: int = 32 * 1024 * 1024):
    events.on_log("scan_started", total=source.size)
    findings = []
    for finding in scan(source, for_categories(categories),
                        chunk_size=chunk_size,
                        on_progress=events.on_progress):
        findings.append(finding)
        events.on_found(finding)
    events.on_log("scan_finished", found=len(findings))
    return findings
