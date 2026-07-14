"""Rebuild playable MJPEG AVI videos from raw MJPEG frames.

This is the technique that recovered the session's 40 camera videos: many
cameras store video as a stream of independent JPEG frames (Motion-JPEG).
When the filesystem is gone the frames survive but the AVI container is lost,
so we collect frames in disk order and mux a fresh, clean AVI around them.
"""
import io
import struct

from almunqith.core.carve.validators.jpeg import validate_jpeg


def _fourcc(s: str) -> bytes:
    return s.encode("ascii")


def build_avi(frames, out, width, height, fps=15.0, audio_chunks=None,
              audio_fmt=None):
    """Mux MJPEG `frames` (list of JPEG byte strings) into an AVI written to
    `out` (a binary file-like). `audio_chunks` is an optional list of raw PCM
    byte strings; `audio_fmt` is (channels, sample_rate, bits) when present.
    Returns the number of video frames written.
    """
    audio_chunks = audio_chunks or []
    n = len(frames)
    us_per_frame = int(1e6 / fps) if fps else 66666
    ch, rate, bits = audio_fmt if (audio_fmt and audio_chunks) else (0, 0, 0)
    block = max(1, ch * (bits // 8)) if ch else 1
    abytes = sum(len(a) for a in audio_chunks)

    # ---- movi chunk (interleaved video/audio) + index ----
    movi = io.BytesIO()
    movi.write(b"movi")
    index = []
    items = [("00dc", f) for f in frames]
    if ch:
        items += [("01wb", a) for a in audio_chunks]
    for cid, data in items:
        index.append((cid.encode("ascii"), movi.tell() - 4, len(data)))
        movi.write(cid.encode("ascii") + struct.pack("<I", len(data)) + data)
        if len(data) & 1:
            movi.write(b"\x00")
    movi_data = movi.getvalue()

    # ---- video stream header ----
    strl_v = io.BytesIO()
    strl_v.write(b"strl")
    strh = struct.pack("<4s4sIHHIIIIIIIi4H", _fourcc("vids"), _fourcc("MJPG"),
                       0, 0, 0, 0, 100, int(fps * 100) if fps else 1500, 0, n,
                       1024 * 1024, 0xFFFFFFFF & -1, 0, 0, 0, width, height)
    strl_v.write(b"strh" + struct.pack("<I", len(strh)) + strh)
    bmi = struct.pack("<IiiHH4sIiiII", 40, width, height, 1, 24,
                      _fourcc("MJPG"), width * height * 3, 0, 0, 0, 0)
    strl_v.write(b"strf" + struct.pack("<I", len(bmi)) + bmi)
    strl_v = strl_v.getvalue()
    strls = b"LIST" + struct.pack("<I", len(strl_v)) + strl_v
    n_streams = 1

    # ---- optional audio stream header ----
    if ch:
        strl_a = io.BytesIO()
        strl_a.write(b"strl")
        strh_a = struct.pack("<4s4sIHHIIIIIIIi4H", _fourcc("auds"), b"\x00" * 4,
                             0, 0, 0, 0, block, rate * block, 0,
                             abytes // block if block else abytes, 65536,
                             0xFFFFFFFF & -1, block, 0, 0, 0, 0)
        strl_a.write(b"strh" + struct.pack("<I", len(strh_a)) + strh_a)
        wf = struct.pack("<HHIIHH", 1, ch, rate, rate * block, block, bits)
        strl_a.write(b"strf" + struct.pack("<I", len(wf)) + wf)
        strl_a = strl_a.getvalue()
        strls += b"LIST" + struct.pack("<I", len(strl_a)) + strl_a
        n_streams = 2

    avih = struct.pack("<IIIIIIIIIIIIII", us_per_frame, 3 * 1024 * 1024, 0,
                       0x10, n, 0, n_streams, 1024 * 1024, width, height,
                       0, 0, 0, 0)
    hdrl = b"hdrl" + b"avih" + struct.pack("<I", len(avih)) + avih + strls
    hdr = b"LIST" + struct.pack("<I", len(hdrl)) + hdrl

    idx = io.BytesIO()
    for cid, off, size in index:
        idx.write(cid + struct.pack("<III", 0x10, off, size))
    idx_data = idx.getvalue()

    body = (hdr + b"LIST" + struct.pack("<I", len(movi_data)) + movi_data
            + b"idx1" + struct.pack("<I", len(idx_data)) + idx_data)
    out.write(b"RIFF" + struct.pack("<I", len(body) + 4) + b"AVI " + body)
    return n


_KNOWN = (set(range(0xC0, 0xD0)) | {0xDA, 0xDB, 0xDD, 0xFE, 0x01}
          | set(range(0xE0, 0xF0)))


def scan_frames(source, start, end, *, min_frame=4096, max_frame=2 * 1024 * 1024):
    """Yield (offset, size, width, height) for MJPEG frames between byte
    offsets [start, end) in a source. Uses the fill-tolerant JPEG walker."""
    CH = 16 * 1024 * 1024
    pos = start
    cur_end = start
    while pos < end:
        chunk = source.read_at(pos, min(CH, end - pos) + 3)
        if not chunk:
            break
        local = 0
        while True:
            at = chunk.find(b"\xff\xd8\xff", local)
            if at == -1 or at >= len(chunk) - 3:
                break
            abs_off = pos + at
            if abs_off < cur_end:
                local = at + 1
                continue
            probe = source.read_at(abs_off, max_frame)
            r = validate_jpeg(probe)
            if r.complete and r.end >= min_frame:
                yield (abs_off, r.end, r.meta.get("width", 0),
                       r.meta.get("height", 0))
                cur_end = abs_off + r.end
                local = at + r.end
            else:
                local = at + 1
        pos += CH


def _find_avi_headers(source, start, end):
    """Return sorted absolute offsets of RIFF..AVI container headers, which mark
    where each original camera video began — used as segment split points."""
    offsets = []
    CH = 16 * 1024 * 1024
    pos = start
    while pos < end:
        chunk = source.read_at(pos, min(CH, end - pos) + 12)
        if not chunk:
            break
        at = 0
        while True:
            at = chunk.find(b"RIFF", at)
            if at == -1 or at + 12 > len(chunk):
                break
            if chunk[at + 8:at + 12] == b"AVI ":
                offsets.append(pos + at)
            at += 4
        pos += CH
    return sorted(set(offsets))


def rebuild_videos(source, start, end, out_dir, on_event=lambda k, **kw: None,
                   min_run=30):
    """Scan [start, end) for MJPEG frames, split into separate videos at each
    original AVI header boundary (and on large gaps / dimension changes), and
    write playable AVIs to out_dir. Returns list of (path, frame_count)."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    frames = list(scan_frames(source, start, end))
    on_event("frames_found", count=len(frames))
    headers = _find_avi_headers(source, start, end)
    videos = []
    run = []
    last_end = None
    dims = None
    idx = 0
    hi = 0

    def flush():
        nonlocal idx
        if len(run) < min_run:
            return
        idx += 1
        w, h = dims or (640, 480)
        path = os.path.join(out_dir, f"video_{idx:03d}.avi")
        with open(path, "wb") as f:
            data = [source.read_at(o, s) for o, s, _w, _h in run]
            n = build_avi(data, f, w, h)
        videos.append((path, n))
        on_event("video_built", path=path, frames=n)

    for off, size, w, h in frames:
        crossed_header = False
        while hi < len(headers) and headers[hi] <= off:
            crossed_header = True
            hi += 1
        gap = last_end is not None and off - last_end > 256 * 1024
        newdim = dims is not None and w and (w, h) != dims
        if run and (crossed_header or gap or newdim):
            flush()
            run = []
            dims = None
        if w:
            dims = (w, h)
        run.append((off, size, w, h))
        last_end = off + size
    flush()
    return videos
