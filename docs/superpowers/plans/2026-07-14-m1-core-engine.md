# AlMunqith M1 — Core Recovery Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the testable core of AlMunqith: read sources (image files / raw devices) resiliently, carve photos & videos by signature with fill-tolerant validators, and extract findings to categorized folders — pure Python, fully covered by pytest, no GUI yet.

**Architecture:** A `Source` abstraction (DiskImage / RawDevice) feeds a watchdog-guarded `ResilientReader`; `scanner.scan()` streams chunks, matches signature magics at any byte offset, validates candidates with per-format walkers (ported from the proven session tools), and yields `Finding`s; `pipeline.run_scan()` orchestrates with an events callback protocol; `extract.extract()` writes categorized output + report. `devices.list_drives()` enumerates Windows disks for the future UI.

**Tech Stack:** Python 3.11 (venv at `D:\AlMunqith\.venv`), pytest, Pillow (test fixtures + future thumbnails). No PySide6 in M1. No network anywhere.

## Global Constraints

- Python 3.11, venv: `D:\AlMunqith\.venv`; run tests with `D:\AlMunqith\.venv\Scripts\python.exe -m pytest`.
- Package root: `D:\AlMunqith\almunqith\`; tests in `D:\AlMunqith\tests\`.
- **Read-only source rule:** no code path may open a source (device or image under recovery) with write access — `open(..., 'rb')` / `GENERIC_READ` only.
- No network calls anywhere in the codebase.
- All identifiers/comments in English; user-facing strings deferred to M2 i18n.
- Every commit runs from `D:\AlMunqith` and ends with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Windows paths in commands use backslashes; git bash commands use forward slashes.

---

### Task 1: Project scaffold + pytest harness

**Files:**
- Create: `pyproject.toml`, `almunqith/__init__.py`, `almunqith/core/__init__.py`, `almunqith/core/carve/__init__.py`, `almunqith/core/carve/validators/__init__.py`, `tests/__init__.py`, `tests/test_scaffold.py`

**Interfaces:**
- Consumes: nothing
- Produces: importable package `almunqith` (version string `almunqith.__version__ = "0.1.0"`), working pytest command for all later tasks.

- [ ] **Step 1: Create venv and install deps**

Run (PowerShell, from `D:\AlMunqith`):
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --quiet pytest pillow
```
Expected: exit 0. (`python` = the available Python 3.11.)

- [ ] **Step 2: Write the failing test**

`tests/test_scaffold.py`:
```python
import almunqith


def test_package_importable_with_version():
    assert almunqith.__version__ == "0.1.0"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_scaffold.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'almunqith'`)

- [ ] **Step 4: Write minimal implementation**

`pyproject.toml`:
```toml
[project]
name = "almunqith"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["pillow"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`almunqith/__init__.py`:
```python
__version__ = "0.1.0"
```

Create empty `__init__.py` files: `almunqith/core/__init__.py`, `almunqith/core/carve/__init__.py`, `almunqith/core/carve/validators/__init__.py`, `tests/__init__.py`.

Install the package editable so tests import it:
```powershell
.\.venv\Scripts\python.exe -m pip install --quiet -e .
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_scaffold.py -v`
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "chore: scaffold almunqith package with pytest harness

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: DiskImage source

**Files:**
- Create: `almunqith/core/source.py`
- Test: `tests/test_source.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `class DiskImage:` `__init__(self, path)`, attribute `size: int`, `read_at(self, offset: int, length: int) -> bytes` (returns fewer/empty bytes past EOF, never raises for out-of-range), `close()`, context-manager support.
  - Module constant `SECTOR = 512`.

- [ ] **Step 1: Write the failing test**

`tests/test_source.py`:
```python
import os
from almunqith.core.source import DiskImage


def test_diskimage_reads_at_offset(tmp_path):
    p = tmp_path / "disk.img"
    p.write_bytes(b"A" * 100 + b"HELLO" + b"B" * 100)
    with DiskImage(p) as src:
        assert src.size == 205
        assert src.read_at(100, 5) == b"HELLO"
        assert src.read_at(0, 3) == b"AAA"


def test_diskimage_read_past_eof_returns_short(tmp_path):
    p = tmp_path / "disk.img"
    p.write_bytes(b"X" * 10)
    with DiskImage(p) as src:
        assert src.read_at(8, 100) == b"XX"
        assert src.read_at(500, 4) == b""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_source.py -v`
Expected: FAIL (`ImportError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/source.py`:
```python
"""Read-only data sources for recovery: image files and raw devices."""
import os

SECTOR = 512


class DiskImage:
    def __init__(self, path):
        self._f = open(path, "rb")          # read-only, per project rule
        self._f.seek(0, os.SEEK_END)
        self.size = self._f.tell()

    def read_at(self, offset: int, length: int) -> bytes:
        if offset >= self.size:
            return b""
        self._f.seek(offset)
        return self._f.read(length)

    def close(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_source.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(core): DiskImage read-only source

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: RawDevice source with sector alignment

**Files:**
- Modify: `almunqith/core/source.py` (append class)
- Test: `tests/test_source.py` (append tests)

**Interfaces:**
- Consumes: `SECTOR` from Task 2.
- Produces: `class RawDevice:` `__init__(self, path: str, size: int)`, `size: int`, `read_at(offset, length) -> bytes`, `close()`, context manager. Internally all OS reads are sector-aligned (`_read_aligned`); subclasses/tests may override `_os_read(self, aligned_offset: int, aligned_length: int) -> bytes`. Live Windows use: `RawDevice(r"\\.\PhysicalDrive1", size=...)` opened `'rb', buffering=0`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_source.py`:
```python
from almunqith.core.source import RawDevice, SECTOR


class FakeRaw(RawDevice):
    """RawDevice whose backing store is a bytes buffer (no real device)."""

    def __init__(self, data: bytes):
        self._data = data
        self.size = len(data)

    def _os_read(self, aligned_offset, aligned_length):
        assert aligned_offset % SECTOR == 0, "unaligned offset reached OS"
        assert aligned_length % SECTOR == 0, "unaligned length reached OS"
        return self._data[aligned_offset:aligned_offset + aligned_length]

    def close(self):
        pass


def test_rawdevice_unaligned_read_is_trimmed_correctly():
    data = bytes(range(256)) * 8  # 2048 bytes = 4 sectors
    dev = FakeRaw(data)
    assert dev.read_at(5, 10) == data[5:15]
    assert dev.read_at(510, 600) == data[510:1110]
    assert dev.read_at(0, 512) == data[:512]


def test_rawdevice_read_clamped_to_size():
    data = b"Z" * 1024
    dev = FakeRaw(data)
    assert dev.read_at(1000, 500) == data[1000:]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_source.py -v`
Expected: FAIL (`ImportError: cannot import name 'RawDevice'`)

- [ ] **Step 3: Write minimal implementation**

Append to `almunqith/core/source.py`:
```python
class RawDevice:
    """Raw block device; OS reads must be sector-aligned on Windows."""

    def __init__(self, path: str, size: int):
        self._f = open(path, "rb", buffering=0)   # read-only, per project rule
        self.size = size

    def _os_read(self, aligned_offset: int, aligned_length: int) -> bytes:
        self._f.seek(aligned_offset)
        return self._f.read(aligned_length)

    def read_at(self, offset: int, length: int) -> bytes:
        if offset >= self.size:
            return b""
        length = min(length, self.size - offset)
        start = (offset // SECTOR) * SECTOR
        end_unaligned = offset + length
        end = ((end_unaligned + SECTOR - 1) // SECTOR) * SECTOR
        end = min(end, ((self.size + SECTOR - 1) // SECTOR) * SECTOR)
        raw = self._os_read(start, end - start)
        return raw[offset - start:offset - start + length]

    def close(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_source.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(core): RawDevice source with sector-aligned reads

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: ResilientReader — watchdog reads with gap tracking

**Files:**
- Create: `almunqith/core/reader.py`
- Test: `tests/test_reader.py`

**Interfaces:**
- Consumes: any Source (`.read_at`, `.size`).
- Produces:
  - `@dataclass Gap: start: int; end: int; reason: str`
  - `class ResilientReader:` `__init__(self, source, timeout_s: float = 25.0, reopen: Callable[[], object] | None = None, on_event: Callable[[str, dict], None] | None = None)`; `size` property mirroring source; `read_at(offset, length) -> bytes | None` — `None` means unreadable (gap recorded in `self.gaps: list[Gap]`); on first timeout calls `reopen()` (if given) to get a fresh source and retries once.
  - Event keys emitted via `on_event(key, data)`: `"read_timeout"`, `"reopened"`, `"gap_recorded"`.

- [ ] **Step 1: Write the failing test**

`tests/test_reader.py`:
```python
import threading
from almunqith.core.reader import ResilientReader, Gap


class GoodSource:
    size = 4096

    def read_at(self, offset, length):
        return b"G" * length


class HangingSource:
    """Blocks forever on a chosen offset, normal elsewhere."""
    size = 4096

    def __init__(self, hang_offset):
        self.hang_offset = hang_offset
        self.release = threading.Event()

    def read_at(self, offset, length):
        if offset == self.hang_offset:
            self.release.wait(10)
        return b"H" * length


def test_normal_reads_pass_through():
    r = ResilientReader(GoodSource(), timeout_s=1.0)
    assert r.read_at(0, 100) == b"G" * 100
    assert r.gaps == []


def test_hang_then_reopen_recovers():
    events = []
    reopened = GoodSource()
    r = ResilientReader(HangingSource(hang_offset=512), timeout_s=0.2,
                        reopen=lambda: reopened,
                        on_event=lambda k, d: events.append(k))
    assert r.read_at(512, 64) == b"G" * 64      # retried on fresh source
    assert "read_timeout" in events and "reopened" in events
    assert r.gaps == []


def test_hang_without_reopen_records_gap():
    r = ResilientReader(HangingSource(hang_offset=0), timeout_s=0.2)
    assert r.read_at(0, 64) is None
    assert r.gaps == [Gap(start=0, end=64, reason="hang")]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_reader.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/reader.py`:
```python
"""Watchdog-guarded reading with automatic reopen and gap tracking.

Ported from the proven rescue imager (session 2026-07-14): a read that
hangs is abandoned (its thread is left to die), the source is reopened
via the caller-provided factory, and the read retried once. Persistent
failure records a Gap instead of blocking recovery forever.
"""
import queue
import threading
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Gap:
    start: int
    end: int
    reason: str


class ResilientReader:
    def __init__(self, source, timeout_s: float = 25.0,
                 reopen: Optional[Callable[[], object]] = None,
                 on_event: Optional[Callable[[str, dict], None]] = None):
        self._source = source
        self._timeout = timeout_s
        self._reopen = reopen
        self._on_event = on_event or (lambda k, d: None)
        self.gaps: list[Gap] = []

    @property
    def size(self) -> int:
        return self._source.size

    def _timed_read(self, offset: int, length: int):
        q: queue.Queue = queue.Queue()
        src = self._source

        def worker():
            try:
                q.put(src.read_at(offset, length))
            except Exception as e:            # noqa: BLE001 - any IO failure is a gap candidate
                q.put(e)

        threading.Thread(target=worker, daemon=True).start()
        try:
            return q.get(timeout=self._timeout)
        except queue.Empty:
            return TimeoutError()

    def read_at(self, offset: int, length: int):
        result = self._timed_read(offset, length)
        if isinstance(result, bytes):
            return result
        self._on_event("read_timeout", {"offset": offset})
        if self._reopen is not None:
            self._source = self._reopen()
            self._on_event("reopened", {})
            result = self._timed_read(offset, length)
            if isinstance(result, bytes):
                return result
        reason = "hang" if isinstance(result, TimeoutError) else "error"
        self.gaps.append(Gap(start=offset, end=offset + length, reason=reason))
        self._on_event("gap_recorded", {"start": offset, "end": offset + length})
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_reader.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(core): ResilientReader watchdog with reopen and gap tracking

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: JPEG validator (fill-tolerant walker)

**Files:**
- Create: `almunqith/core/carve/validators/jpeg.py`, `tests/helpers.py`
- Test: `tests/test_validator_jpeg.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `@dataclass ValidationResult: end: int; complete: bool; meta: dict` (defined in `almunqith/core/carve/validators/jpeg.py` for now; Task 8 re-exports it from `signatures.py`).
  - `validate_jpeg(data: bytes) -> ValidationResult` — `meta` contains `width`/`height` when SOF seen. Tolerates runs of 0xFF fill bytes between segments and inside entropy scan (the exact behavior that rescued the session's 40 videos).
  - `tests/helpers.py: make_jpeg(w=64, h=48) -> bytes` — real JPEG bytes via Pillow with pseudo-random pixels.

- [ ] **Step 1: Write the failing test**

`tests/helpers.py`:
```python
import io
import random
from PIL import Image


def make_jpeg(w=64, h=48) -> bytes:
    rnd = random.Random(42)
    img = Image.new("RGB", (w, h))
    img.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256))
                 for _ in range(w * h)])
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()
```

`tests/test_validator_jpeg.py`:
```python
from almunqith.core.carve.validators.jpeg import validate_jpeg
from tests.helpers import make_jpeg


def test_clean_jpeg_is_complete_with_dimensions():
    data = make_jpeg(64, 48)
    r = validate_jpeg(data + b"\x00" * 100)   # trailing junk beyond EOI
    assert r.complete is True
    assert r.end == len(data)
    assert r.meta["width"] == 64 and r.meta["height"] == 48


def test_ff_fill_runs_between_segments_are_tolerated():
    data = make_jpeg()
    # inject 4 fill bytes before the second marker segment (after SOI)
    filled = data[:2] + b"\xff\xff\xff\xff" + data[2:]
    r = validate_jpeg(filled)
    assert r.complete is True
    assert r.end == len(filled)


def test_truncated_jpeg_is_incomplete():
    data = make_jpeg()
    r = validate_jpeg(data[: len(data) // 2])
    assert r.complete is False


def test_garbage_after_header_reports_break_offset():
    data = make_jpeg()
    corrupted = data[:20] + b"\x12\x34" + data[22:]
    r = validate_jpeg(corrupted)
    assert r.complete is False
    assert 0 < r.end <= 22
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validator_jpeg.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/carve/validators/jpeg.py`:
```python
"""Fill-tolerant JPEG structure walker (ported from session rebuild tool)."""
import struct
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    end: int
    complete: bool
    meta: dict = field(default_factory=dict)


_KNOWN = (set(range(0xC0, 0xD0)) | {0xDA, 0xDB, 0xDD, 0xFE, 0x01}
          | set(range(0xE0, 0xF0)))


def validate_jpeg(data: bytes) -> ValidationResult:
    meta: dict = {}
    if data[:3] != b"\xff\xd8\xff":
        return ValidationResult(0, False, meta)
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            return ValidationResult(i, False, meta)
        while i + 1 < len(data) and data[i + 1] == 0xFF:   # legal fill bytes
            i += 1
        m = data[i + 1]
        if m == 0xD9:
            return ValidationResult(i + 2, True, meta)
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        if m not in _KNOWN:
            return ValidationResult(i, False, meta)
        seglen = struct.unpack_from(">H", data, i + 2)[0]
        if seglen < 2:
            return ValidationResult(i, False, meta)
        if m in (0xC0, 0xC1, 0xC2, 0xC3) and i + 9 < len(data):
            meta["height"] = struct.unpack_from(">H", data, i + 5)[0]
            meta["width"] = struct.unpack_from(">H", data, i + 7)[0]
        if m == 0xDA:
            j = i + 2 + seglen
            resumed = False
            while True:
                k = data.find(b"\xff", j)
                if k == -1 or k + 1 >= len(data):
                    return ValidationResult(len(data), False, meta)
                n = data[k + 1]
                if n == 0x00 or 0xD0 <= n <= 0xD7:
                    j = k + 2
                    continue
                if n == 0xFF:
                    j = k + 1
                    continue
                if n == 0xD9:
                    return ValidationResult(k + 2, True, meta)
                if n in _KNOWN:
                    i = k
                    resumed = True
                    break
                return ValidationResult(k, False, meta)
            if resumed:
                continue
        i += 2 + seglen
    return ValidationResult(i, False, meta)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validator_jpeg.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(carve): fill-tolerant JPEG validator with dimension extraction

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: PNG validator

**Files:**
- Create: `almunqith/core/carve/validators/png.py`
- Test: `tests/test_validator_png.py`

**Interfaces:**
- Consumes: `ValidationResult` from `almunqith.core.carve.validators.jpeg`.
- Produces: `validate_png(data: bytes) -> ValidationResult` — walks chunks (length/type/data/CRC) to `IEND`; `meta` gets `width`/`height` from IHDR; CRC of IHDR verified (cheap integrity signal).

- [ ] **Step 1: Write the failing test**

`tests/test_validator_png.py`:
```python
import io
from PIL import Image
from almunqith.core.carve.validators.png import validate_png


def _make_png(w=32, h=16) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (10, 200, 50)).save(buf, "PNG")
    return buf.getvalue()


def test_clean_png_complete_with_dimensions():
    data = _make_png(32, 16)
    r = validate_png(data + b"JUNKJUNK")
    assert r.complete is True
    assert r.end == len(data)
    assert r.meta == {"width": 32, "height": 16}


def test_truncated_png_incomplete():
    data = _make_png()
    r = validate_png(data[:40])
    assert r.complete is False


def test_corrupted_ihdr_crc_rejected():
    data = bytearray(_make_png())
    data[20] ^= 0xFF                     # flip a byte inside IHDR data
    r = validate_png(bytes(data))
    assert r.complete is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validator_png.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/carve/validators/png.py`:
```python
"""PNG chunk-walk validator."""
import struct
import zlib

from almunqith.core.carve.validators.jpeg import ValidationResult

_SIG = b"\x89PNG\r\n\x1a\n"


def validate_png(data: bytes) -> ValidationResult:
    meta: dict = {}
    if not data.startswith(_SIG):
        return ValidationResult(0, False, meta)
    i = len(_SIG)
    first = True
    while i + 12 <= len(data):
        length = struct.unpack_from(">I", data, i)[0]
        ctype = data[i + 4:i + 8]
        if length > 0x7FFFFFFF or not ctype.isalpha():
            return ValidationResult(i, False, meta)
        end = i + 12 + length
        if end > len(data):
            return ValidationResult(len(data), False, meta)
        if first:
            if ctype != b"IHDR" or length != 13:
                return ValidationResult(i, False, meta)
            crc = struct.unpack_from(">I", data, i + 8 + length)[0]
            if zlib.crc32(data[i + 4:i + 8 + length]) & 0xFFFFFFFF != crc:
                return ValidationResult(i, False, meta)
            meta["width"], meta["height"] = struct.unpack_from(">II", data, i + 8)
            first = False
        if ctype == b"IEND":
            return ValidationResult(end, True, meta)
        i = end
    return ValidationResult(min(i, len(data)), False, meta)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validator_png.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(carve): PNG validator with IHDR CRC check

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: RIFF/AVI and MP4/MOV validators

**Files:**
- Create: `almunqith/core/carve/validators/riff.py`, `almunqith/core/carve/validators/mp4.py`
- Test: `tests/test_validator_video.py`

**Interfaces:**
- Consumes: `ValidationResult` from jpeg module.
- Produces:
  - `validate_riff(data) -> ValidationResult` — requires `RIFF<size>AVI ` or `RIFF<size>WAVE`; `end = 8 + declared_size` clamped to window; `complete` iff the declared span fits the window; `meta["variant"]` is `"avi"`/`"wave"`.
  - `validate_mp4(data) -> ValidationResult` — data starts at box-aligned `ftyp` minus 4 (i.e. candidate start = magic hit − 4); walks ISO-BMFF boxes; `complete` iff boxes chain cleanly through the window end or a final box; requires seeing `moov` or `mdat`; `meta["brand"]` from ftyp.

- [ ] **Step 1: Write the failing test**

`tests/test_validator_video.py`:
```python
import struct
from almunqith.core.carve.validators.riff import validate_riff
from almunqith.core.carve.validators.mp4 import validate_mp4


def _riff(variant=b"AVI ", payload=b"x" * 100):
    return b"RIFF" + struct.pack("<I", len(payload) + 4) + variant + payload


def _box(name: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + name + payload


def test_riff_avi_complete():
    data = _riff() + b"TRAILING"
    r = validate_riff(data)
    assert r.complete is True
    assert r.end == 8 + 104
    assert r.meta["variant"] == "avi"


def test_riff_declared_beyond_window_incomplete():
    data = b"RIFF" + struct.pack("<I", 10_000_000) + b"AVI " + b"x" * 50
    r = validate_riff(data)
    assert r.complete is False


def test_riff_wrong_fourcc_rejected():
    assert validate_riff(_riff(variant=b"XXXX")).end == 0


def test_mp4_box_chain_complete():
    data = (_box(b"ftyp", b"isom\x00\x00\x02\x00isomiso2")
            + _box(b"moov", b"m" * 40)
            + _box(b"mdat", b"d" * 200))
    r = validate_mp4(data)
    assert r.complete is True
    assert r.end == len(data)
    assert r.meta["brand"] == "isom"


def test_mp4_without_moov_or_mdat_incomplete():
    data = _box(b"ftyp", b"isom\x00\x00\x02\x00") + b"\x00" * 64
    r = validate_mp4(data)
    assert r.complete is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validator_video.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/carve/validators/riff.py`:
```python
"""RIFF container validator (AVI, WAV)."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult

_VARIANTS = {b"AVI ": "avi", b"WAVE": "wave"}


def validate_riff(data: bytes) -> ValidationResult:
    if len(data) < 12 or data[:4] != b"RIFF":
        return ValidationResult(0, False, {})
    variant = _VARIANTS.get(data[8:12])
    if variant is None:
        return ValidationResult(0, False, {})
    declared = struct.unpack_from("<I", data, 4)[0]
    end = 8 + declared
    meta = {"variant": variant}
    if declared < 4 or end > len(data):
        return ValidationResult(min(end, len(data)), False, meta)
    return ValidationResult(end, True, meta)
```

`almunqith/core/carve/validators/mp4.py`:
```python
"""ISO-BMFF (MP4/MOV/3GP/HEIC container) box-walk validator."""
import struct

from almunqith.core.carve.validators.jpeg import ValidationResult

_TOP_BOXES = {b"ftyp", b"moov", b"mdat", b"free", b"skip", b"wide",
              b"pdin", b"moof", b"mfra", b"meta", b"uuid", b"styp", b"sidx"}


def validate_mp4(data: bytes) -> ValidationResult:
    meta: dict = {}
    if len(data) < 12 or data[4:8] != b"ftyp":
        return ValidationResult(0, False, meta)
    meta["brand"] = data[8:12].decode("ascii", "replace")
    i = 0
    seen_media = False
    while i + 8 <= len(data):
        size = struct.unpack_from(">I", data, i)[0]
        name = data[i + 4:i + 8]
        if name not in _TOP_BOXES:
            return ValidationResult(i, seen_media and i > 0, meta)
        if size == 1:
            if i + 16 > len(data):
                return ValidationResult(len(data), False, meta)
            size = struct.unpack_from(">Q", data, i + 8)[0]
        elif size == 0:                       # box extends to end of file
            if name in (b"mdat", b"moov"):
                seen_media = True
            return ValidationResult(len(data), False, meta)
        if size < 8:
            return ValidationResult(i, False, meta)
        if name in (b"mdat", b"moov"):
            seen_media = True
        if i + size > len(data):
            return ValidationResult(len(data), False, meta)
        i += size
    return ValidationResult(i, seen_media, meta)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validator_video.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(carve): RIFF and ISO-BMFF validators

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Signature registry

**Files:**
- Create: `almunqith/core/carve/signatures.py`
- Test: `tests/test_signatures.py`

**Interfaces:**
- Consumes: the four validators from Tasks 5-7.
- Produces:
  - Re-export: `from almunqith.core.carve.signatures import ValidationResult`.
  - `@dataclass(frozen=True) Signature: name: str; category: str; extension: str; magics: tuple[bytes, ...]; magic_offset: int; validate: Callable[[bytes], ValidationResult]; min_size: int`
  - `REGISTRY: tuple[Signature, ...]` containing: `jpeg` (category `photos`, magic `\xff\xd8\xff`, offset 0, min_size 2048), `png` (photos, PNG sig, offset 0, min_size 256), `avi` (videos, `RIFF`, offset 0, min_size 8192), `mp4` (videos, `ftyp`, **magic_offset 4**, min_size 8192).
  - `for_categories(categories: set[str]) -> tuple[Signature, ...]` — `{"all"}` returns everything.

- [ ] **Step 1: Write the failing test**

`tests/test_signatures.py`:
```python
from almunqith.core.carve.signatures import REGISTRY, for_categories


def test_registry_has_m1_formats():
    names = {s.name for s in REGISTRY}
    assert {"jpeg", "png", "avi", "mp4"} <= names


def test_mp4_magic_offset_is_4():
    mp4 = next(s for s in REGISTRY if s.name == "mp4")
    assert mp4.magics == (b"ftyp",)
    assert mp4.magic_offset == 4


def test_for_categories_filters():
    photos = for_categories({"photos"})
    assert all(s.category == "photos" for s in photos)
    assert {s.name for s in photos} == {"jpeg", "png"}
    assert len(for_categories({"all"})) == len(REGISTRY)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_signatures.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/carve/signatures.py`:
```python
"""Registry of carveable file signatures (M1: photos + videos)."""
from dataclasses import dataclass
from typing import Callable

from almunqith.core.carve.validators.jpeg import ValidationResult, validate_jpeg
from almunqith.core.carve.validators.png import validate_png
from almunqith.core.carve.validators.riff import validate_riff
from almunqith.core.carve.validators.mp4 import validate_mp4

__all__ = ["ValidationResult", "Signature", "REGISTRY", "for_categories"]


@dataclass(frozen=True)
class Signature:
    name: str
    category: str
    extension: str
    magics: tuple[bytes, ...]
    magic_offset: int
    validate: Callable[[bytes], ValidationResult]
    min_size: int


REGISTRY: tuple[Signature, ...] = (
    Signature("jpeg", "photos", ".jpg", (b"\xff\xd8\xff",), 0, validate_jpeg, 2048),
    Signature("png", "photos", ".png", (b"\x89PNG\r\n\x1a\n",), 0, validate_png, 256),
    Signature("avi", "videos", ".avi", (b"RIFF",), 0, validate_riff, 8192),
    Signature("mp4", "videos", ".mp4", (b"ftyp",), 4, validate_mp4, 8192),
)


def for_categories(categories: set[str]) -> tuple[Signature, ...]:
    if "all" in categories:
        return REGISTRY
    return tuple(s for s in REGISTRY if s.category in categories)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_signatures.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(carve): signature registry for M1 formats

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: Scanner — streaming multi-signature carve

**Files:**
- Create: `almunqith/core/carve/scanner.py`
- Test: `tests/test_scanner.py`

**Interfaces:**
- Consumes: Source protocol (`read_at`, `size`), `Signature`/`for_categories` (Task 8).
- Produces:
  - `@dataclass Finding: offset: int; size: int; signature: Signature; complete: bool; meta: dict`
  - `scan(source, signatures, *, chunk_size=32*1024*1024, window_size=8*1024*1024, on_progress: Callable[[int, int], None] | None = None) -> Iterator[Finding]`
  - Behavior: magics matched at **any byte offset**; candidate start = hit − `magic_offset` (skipped if negative); validation reads a small 256 KiB probe window first and re-reads `window_size` only when the walker ran off the probe's end (keeps hit-dense regions fast); complete findings advance a consumed-watermark so nested hits (e.g. EXIF thumbnails) are not re-emitted; incomplete findings ≥ `min_size` of clean structure are emitted with `complete=False`; progress callback gets `(bytes_scanned, total)`.

- [ ] **Step 1: Write the failing test**

`tests/test_scanner.py`:
```python
import os
import random
from almunqith.core.source import DiskImage
from almunqith.core.carve.signatures import for_categories
from almunqith.core.carve.scanner import scan
from tests.helpers import make_jpeg


def _build_image(tmp_path):
    rnd = random.Random(7)
    filler = bytes(rnd.randrange(256) for _ in range(64 * 1024))
    j1, j2 = make_jpeg(64, 48), make_jpeg(32, 32)
    layout = filler[:1000] + j1 + filler[:333] + j2 + filler
    p = tmp_path / "test.img"
    p.write_bytes(layout)
    return p, [(1000, len(j1)), (1000 + len(j1) + 333, len(j2))]


def test_scan_finds_jpegs_at_odd_offsets(tmp_path):
    p, expected = _build_image(tmp_path)
    with DiskImage(p) as src:
        found = [f for f in scan(src, for_categories({"photos"}))
                 if f.signature.name == "jpeg" and f.complete]
    assert [(f.offset, f.size) for f in found] == expected


def test_scan_reports_progress(tmp_path):
    p, _ = _build_image(tmp_path)
    ticks = []
    with DiskImage(p) as src:
        list(scan(src, for_categories({"photos"}),
                  chunk_size=32 * 1024,
                  on_progress=lambda done, total: ticks.append((done, total))))
    assert ticks and ticks[-1][0] == ticks[-1][1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_scanner.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/carve/scanner.py`:
```python
"""Streaming signature scanner: any-offset magic search + validation."""
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

from almunqith.core.carve.signatures import Signature

_MAX_MAGIC = 16


@dataclass
class Finding:
    offset: int
    size: int
    signature: Signature
    complete: bool
    meta: dict


def scan(source, signatures, *, chunk_size: int = 32 * 1024 * 1024,
         window_size: int = 8 * 1024 * 1024,
         on_progress: Optional[Callable[[int, int], None]] = None
         ) -> Iterator[Finding]:
    total = source.size
    consumed = 0                      # watermark: end of last complete finding
    pos = 0
    while pos < total:
        chunk = source.read_at(pos, chunk_size + _MAX_MAGIC)
        if not chunk:
            break
        hits: list[tuple[int, Signature]] = []
        for sig in signatures:
            for magic in sig.magics:
                at = 0
                while True:
                    at = chunk.find(magic, at, chunk_size)
                    if at == -1:
                        break
                    start = pos + at - sig.magic_offset
                    if start >= 0:
                        hits.append((start, sig))
                    at += 1
        hits.sort(key=lambda t: t[0])
        for start, sig in hits:
            if start < consumed:
                continue
            probe = 256 * 1024
            window = source.read_at(start, probe)
            result = sig.validate(window)
            if (not result.complete and len(window) == probe
                    and result.end >= probe - 2):
                window = source.read_at(start, window_size)
                result = sig.validate(window)
            if result.complete and result.end >= sig.min_size:
                yield Finding(start, result.end, sig, True, result.meta)
                consumed = start + result.end
            elif not result.complete and result.end >= sig.min_size:
                yield Finding(start, result.end, sig, False, result.meta)
        pos += chunk_size
        if on_progress:
            on_progress(min(pos, total), total)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_scanner.py -v`
Expected: 2 passed

- [ ] **Step 5: Run the whole suite**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(carve): streaming any-offset signature scanner

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: Extractor with categorized output + report

**Files:**
- Create: `almunqith/core/extract.py`
- Test: `tests/test_extract.py`

**Interfaces:**
- Consumes: `Finding` (Task 9), Source protocol.
- Produces:
  - `extract(source, findings, dest_dir, on_saved: Callable[[int, int], None] | None = None) -> dict` — copies each finding's bytes into `dest_dir/<CategoryTitle>/<name>` where CategoryTitle is `Photos`/`Videos`, name is `{signature.name}_{index:05d}{extension}` (index per category, 1-based); partial files get suffix `_partial` before the extension; writes `dest_dir/report.txt` (one line per file: name, size, complete/partial, source offset); returns summary dict `{"saved": int, "by_category": dict[str, int], "report_path": str}`.
  - Refuses (raises `ValueError`) if `dest_dir` resolves inside the source path's drive when source is a RawDevice path string — guard implemented as: `extract` takes optional `source_drive: str | None`; if given (e.g. `"E:"`) and `os.path.splitdrive(dest_dir)[0].upper() == source_drive.upper()`, raise.

- [ ] **Step 1: Write the failing test**

`tests/test_extract.py`:
```python
import os
import pytest
from almunqith.core.source import DiskImage
from almunqith.core.carve.signatures import for_categories
from almunqith.core.carve.scanner import scan
from almunqith.core.extract import extract
from tests.helpers import make_jpeg


def test_extract_saves_categorized_files_and_report(tmp_path):
    img = tmp_path / "t.img"
    j = make_jpeg()
    img.write_bytes(b"\x00" * 100 + j + b"\x00" * 50)
    dest = tmp_path / "out"
    with DiskImage(img) as src:
        findings = list(scan(src, for_categories({"photos"})))
        summary = extract(src, findings, str(dest))
    files = os.listdir(dest / "Photos")
    assert files == ["jpeg_00001.jpg"]
    assert (dest / "Photos" / "jpeg_00001.jpg").read_bytes() == j
    assert summary["saved"] == 1
    assert os.path.exists(summary["report_path"])
    assert "jpeg_00001.jpg" in (dest / "report.txt").read_text()


def test_extract_refuses_destination_on_source_drive(tmp_path):
    with pytest.raises(ValueError):
        extract(None, [], r"E:\out", source_drive="E:")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_extract.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/extract.py`:
```python
"""Write findings to a categorized destination folder with a report."""
import os
from collections import defaultdict
from typing import Callable, Optional

_TITLES = {"photos": "Photos", "videos": "Videos",
           "documents": "Documents", "audio": "Audio", "archives": "Archives"}
_COPY_CHUNK = 8 * 1024 * 1024


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
    for f in findings:
        title = _TITLES.get(f.signature.category, "Other")
        folder = os.path.join(dest_dir, title)
        os.makedirs(folder, exist_ok=True)
        counters[f.signature.category] += 1
        suffix = "" if f.complete else "_partial"
        name = (f"{f.signature.name}_{counters[f.signature.category]:05d}"
                f"{suffix}{f.signature.extension}")
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_extract.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(core): categorized extractor with report and source-drive guard

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 11: Pipeline v1 — orchestration + events protocol

**Files:**
- Create: `almunqith/core/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `scan`/`Finding` (Task 9), `for_categories` (Task 8), Source protocol.
- Produces:
  - `class Events:` base class with no-op methods `on_progress(self, done: int, total: int)`, `on_found(self, finding)`, `on_log(self, key: str, **kw)` — UI (M2) subclasses this.
  - `run_scan(source, categories: set[str], events: Events, *, chunk_size: int = 32*1024*1024) -> list[Finding]` — emits `on_log("scan_started", total=...)`, streams findings (calling `on_found` per finding and `on_progress` per chunk), emits `on_log("scan_finished", found=N)`, returns all findings. This is the seam where later milestones bolt on the escalation ladder (levels 0/1/3/4).

- [ ] **Step 1: Write the failing test**

`tests/test_pipeline.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_pipeline.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/pipeline.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_pipeline.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(core): pipeline v1 with events protocol

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 12: Windows drive enumeration

**Files:**
- Create: `almunqith/core/devices.py`
- Test: `tests/test_devices.py`

**Interfaces:**
- Consumes: nothing (subprocess to PowerShell at runtime; tests exercise the pure parser).
- Produces:
  - `@dataclass DriveInfo: number: int; path: str; size: int; bus: str; friendly: str; letters: list[str]; is_system: bool` — `path` is `\\.\PhysicalDriveN`.
  - `parse_drives(disks_json: str, partitions_json: str) -> list[DriveInfo]` — pure function over PowerShell `ConvertTo-Json` output (handles both a single object and a list).
  - `list_drives() -> list[DriveInfo]` — runs `powershell -NoProfile -Command "Get-Disk | Select Number,FriendlyName,BusType,Size,IsBoot | ConvertTo-Json"` and `"Get-Partition | Select DiskNumber,DriveLetter | ConvertTo-Json"`, feeds `parse_drives`.

- [ ] **Step 1: Write the failing test**

`tests/test_devices.py`:
```python
import json
from almunqith.core.devices import parse_drives


DISKS = json.dumps([
    {"Number": 0, "FriendlyName": "Samsung SSD", "BusType": "NVMe",
     "Size": 1024_000_000_000, "IsBoot": True},
    {"Number": 1, "FriendlyName": "Mass Storage Device", "BusType": "USB",
     "Size": 31_457_280_000, "IsBoot": False},
])
PARTS = json.dumps([
    {"DiskNumber": 0, "DriveLetter": "C"},
    {"DiskNumber": 0, "DriveLetter": None},
    {"DiskNumber": 1, "DriveLetter": "E"},
])


def test_parse_drives_maps_letters_and_flags():
    drives = parse_drives(DISKS, PARTS)
    assert len(drives) == 2
    sd = drives[1]
    assert sd.path == r"\\.\PhysicalDrive1"
    assert sd.bus == "USB" and sd.letters == ["E"] and sd.is_system is False
    assert drives[0].is_system is True and drives[0].letters == ["C"]


def test_parse_drives_accepts_single_object():
    single = json.dumps({"Number": 2, "FriendlyName": "X", "BusType": "USB",
                         "Size": 100, "IsBoot": False})
    drives = parse_drives(single, json.dumps([]))
    assert drives[0].number == 2 and drives[0].letters == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_devices.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write minimal implementation**

`almunqith/core/devices.py`:
```python
"""Windows drive enumeration via PowerShell (no external deps)."""
import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class DriveInfo:
    number: int
    path: str
    size: int
    bus: str
    friendly: str
    letters: list = field(default_factory=list)
    is_system: bool = False


def _as_list(js: str):
    if not js.strip():
        return []
    data = json.loads(js)
    return data if isinstance(data, list) else [data]


def parse_drives(disks_json: str, partitions_json: str):
    letters: dict[int, list] = {}
    for p in _as_list(partitions_json):
        letter = p.get("DriveLetter")
        if letter:
            letters.setdefault(p["DiskNumber"], []).append(str(letter))
    drives = []
    for d in _as_list(disks_json):
        n = d["Number"]
        drives.append(DriveInfo(
            number=n,
            path=rf"\\.\PhysicalDrive{n}",
            size=int(d["Size"]),
            bus=str(d.get("BusType", "")),
            friendly=str(d.get("FriendlyName", "")),
            letters=sorted(letters.get(n, [])),
            is_system=bool(d.get("IsBoot", False)),
        ))
    drives.sort(key=lambda x: x.number)
    return drives


def _ps(cmd: str) -> str:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True, text=True, timeout=60)
    return out.stdout


def list_drives():
    disks = _ps("Get-Disk | Select-Object Number,FriendlyName,BusType,Size,IsBoot"
                " | ConvertTo-Json")
    parts = _ps("Get-Partition | Select-Object DiskNumber,DriveLetter"
                " | ConvertTo-Json")
    return parse_drives(disks, parts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_devices.py -v`
Expected: 2 passed

- [ ] **Step 5: Live smoke check (manual, informational)**

Run: `.\.venv\Scripts\python.exe -c "from almunqith.core.devices import list_drives; [print(d) for d in list_drives()]"`
Expected: prints at least the system disk; no exception.

- [ ] **Step 6: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "feat(core): Windows drive enumeration with pure parser

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 13: Golden-sample acceptance smoke (M1 exit test)

**Files:**
- Create: `tests/test_golden_sample.py`

**Interfaces:**
- Consumes: `DiskImage`, `run_scan`, `Events` (Tasks 2, 11).
- Produces: a slow, skippable end-to-end proof that the M1 engine finds real camera frames in the real rescued card image.

- [ ] **Step 1: Write the test (it should pass immediately — this is an acceptance gate, not TDD)**

`tests/test_golden_sample.py`:
```python
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
```

- [ ] **Step 2: Run it**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_golden_sample.py -v`
Expected: PASS (or SKIP on machines without the golden image). If it FAILS, the scanner has a real-world regression — stop and fix before closing M1.

- [ ] **Step 3: Run the full suite one last time**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: all pass (golden test may skip elsewhere)

- [ ] **Step 4: Commit**

```bash
cd /d/AlMunqith && git add -A && git commit -m "test: golden-sample acceptance smoke for M1 engine

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## M1 Definition of Done

- `pytest -q` green (≥ 20 tests).
- Golden-sample smoke finds >1000 real frames in the rescued card image.
- No code path opens a source writable; no network imports (`socket`, `urllib`, `requests`) anywhere in `almunqith/`.
- Next: M2 plan (wizard UI wired to `pipeline.run_scan` + `extract`) written as a separate plan document.
