# AlMunqith M3 — More Signatures + Filesystem Undelete

**Goal:** Broaden the carver to 25+ file types with real validators, and add filesystem-aware undelete for FAT32/exFAT/NTFS so recovered files keep their original names and dates when the metadata survives.

**Architecture:** New validators under `core/carve/validators/`, all returning the shared `ValidationResult`, registered in `signatures.py`. New `core/fs/` package with `fat.py`, `exfat.py`, `ntfs.py`, each exposing `scan_deleted(source) -> Iterator[RecoveredEntry]`. `pipeline.run_scan` gains a filesystem pre-pass (level 1) that runs before deep carve (level 2) and yields named findings.

**Tech Stack:** same (pure Python, pytest). No new deps.

## Global Constraints
- Same as M1/M2 (read-only, no network, venv, offscreen for any qt test).
- Every validator returns `almunqith.core.carve.signatures.ValidationResult`.
- Commits end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: GIF + BMP + TIFF validators
Register `gif`, `bmp`, `tiff` (photos). Tests with Pillow-generated fixtures.

### Task 2: PDF + ZIP-family (docx/xlsx/pptx/zip) + OLE2 (doc/xls/ppt)
`pdf` walks `%PDF` … `%%EOF`; `zip` reads End-Of-Central-Directory, sniffs `[Content_Types].xml` to tag docx/xlsx/pptx; `ole2` validates the compound-file header + FAT. Category `documents`/`archives`.

### Task 3: Audio — MP3 (frame sync), WAV (RIFF), FLAC, OGG
`mp3` validates a run of MPEG audio frames; `wav` reuses RIFF; `flac`/`ogg` by header + frame/page structure. Category `audio`.

### Task 4: Remaining video — MKV/WebM (EBML), WMV/ASF, 3GP
`mkv` walks EBML ids; `asf` checks the ASF header GUID + object chain; 3GP via existing mp4 box-walker with brand check.

### Task 5: RAW camera + misc — CR2/NEF/ARW (TIFF-based), HEIC (ISO-BMFF), PSD, RAR/7Z
Extend tiff/mp4 walkers; add `psd` (8BPS header+len), `rar` (Rar!\x1a\x07), `7z` (7z\xBC\xAF).

### Task 6: FAT32/exFAT undelete
`core/fs/fat.py`: parse BPB, walk root+subdir entries, collect entries with 0xE5 first byte (deleted) whose cluster chain is intact; `core/fs/exfat.py`: parse exFAT directory entries (file+stream+name), detect InUse=0. Yield `RecoveredEntry(name, size, first_cluster, mtime, contiguous)`.

### Task 7: NTFS undelete
`core/fs/ntfs.py`: scan for `FILE` records, parse `$FILE_NAME` + `$DATA` (resident and non-resident data runs), flag records whose in-use flag is clear. Yield `RecoveredEntry` with original name/timestamps.

### Task 8: Wire FS pre-pass into pipeline
`pipeline.run_scan` runs `fs.scan_all(source)` first (level 1), converts `RecoveredEntry` → `Finding` with `meta={name,mtime}`; extractor uses `meta["name"]` when present instead of a generated name; dedupe against carved findings by offset. Golden acceptance still passes.

## M3 Definition of Done
- ≥ 25 signatures registered; each has a validator with ≥1 passing fixture test.
- FAT/exFAT/NTFS undelete each recover named entries from a synthetic filesystem image built in-test.
- Full suite green; golden card image still yields its frames.
