"""Write findings to a categorized destination folder with a report."""
import os
from collections import defaultdict
from typing import Callable, Optional

_TITLES = {"photos": "Photos", "videos": "Videos", "documents": "Documents",
           "audio": "Audio", "archives": "Archives", "other": "Other"}
_COPY_CHUNK = 8 * 1024 * 1024
_BAD_CHARS = '<>:"/\\|?*'


def _safe_name(name: str) -> str:
    out = "".join("_" if c in _BAD_CHARS or ord(c) < 32 else c for c in name)
    return out.strip() or "file"


def extract(source, findings, dest_dir: str,
            on_saved: Optional[Callable[[int, int], None]] = None,
            source_drive: Optional[str] = None) -> dict:
    if source_drive and \
            os.path.splitdrive(dest_dir)[0].upper() == source_drive.upper():
        raise ValueError("destination must not be on the source drive")
    os.makedirs(dest_dir, exist_ok=True)
    counters: dict[str, int] = defaultdict(int)
    lines = []
    saved = 0
    used_names: set[str] = set()
    for f in findings:
        title = _TITLES.get(f.signature.category, "Other")
        folder = os.path.join(dest_dir, title)
        os.makedirs(folder, exist_ok=True)
        counters[f.signature.category] += 1
        original = f.meta.get("name") if isinstance(f.meta, dict) else None
        if original:
            name = _safe_name(original)
            if name in used_names:                    # avoid collisions
                stem, ext = os.path.splitext(name)
                name = f"{stem}_{counters[f.signature.category]:05d}{ext}"
        else:
            suffix = "" if f.complete else "_partial"
            name = (f"{f.signature.name}_{counters[f.signature.category]:05d}"
                    f"{suffix}{f.signature.extension}")
        used_names.add(name)
        path = os.path.join(folder, name)
        with open(path, "wb") as out:
            remaining, off = f.size, f.offset
            while remaining > 0:
                data = source.read_at(off, min(_COPY_CHUNK, remaining))
                if not data:
                    break
                out.write(data)
                off += len(data)
                remaining -= len(data)
        lines.append(f"{name}\t{f.size}\t"
                     f"{'complete' if f.complete else 'partial'}\t"
                     f"offset={f.offset}")
        saved += 1
        if on_saved:
            on_saved(saved, len(findings))
    report_path = os.path.join(dest_dir, "report.txt")
    with open(report_path, "w", encoding="utf-8") as r:
        r.write("\n".join(lines))
    return {"saved": saved, "by_category": dict(counters),
            "report_path": report_path}
