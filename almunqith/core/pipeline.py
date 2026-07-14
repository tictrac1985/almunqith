"""Recovery pipeline (escalation ladder).

Level 1 — filesystem undelete (FAT/exFAT/NTFS): recovers files *with* their
original names and dates when directory/MFT metadata survives.
Level 2 — deep signature carve: finds files by content at any byte offset,
the fallback that rescued the session's videos.

run_scan runs level 1 then level 2, de-duplicating carved hits that fall
inside an already-recovered named file.
"""
from almunqith.core.carve.scanner import scan, Finding
from almunqith.core.carve.signatures import for_categories, signature_for_name
from almunqith.core.fs import scan as fs_scan


class Events:
    def on_progress(self, done: int, total: int):
        pass

    def on_found(self, finding):
        pass

    def on_log(self, key: str, **kw):
        pass


def _entry_to_finding(entry) -> Finding:
    sig = signature_for_name(entry.name)
    return Finding(entry.first_offset, entry.size, sig, True,
                   {"name": entry.name, "mtime": entry.mtime, "fs": entry.fs})


def run_scan(source, categories: set, events: Events,
             *, chunk_size: int = 32 * 1024 * 1024, use_fs: bool = True):
    events.on_log("scan_started", total=source.size)
    findings = []
    spans = []            # (start, end) of named files, to dedupe carve hits

    if use_fs:
        try:
            entries = fs_scan.scan_all(source)
        except Exception:
            entries = []
        if entries:
            events.on_log("fs_found", count=len(entries))
        for e in entries:
            f = _entry_to_finding(e)
            if categories != {"all"} and f.signature.category not in categories \
                    and f.signature.category != "other":
                continue
            findings.append(f)
            spans.append((f.offset, f.offset + f.size))
            events.on_found(f)

    def _inside_named(off):
        return any(a <= off < b for a, b in spans)

    for finding in scan(source, for_categories(categories),
                        chunk_size=chunk_size,
                        on_progress=events.on_progress):
        if _inside_named(finding.offset):
            continue
        findings.append(finding)
        events.on_found(finding)

    events.on_log("scan_finished", found=len(findings))
    return findings
