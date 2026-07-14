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
            if result.complete:
                # a fully validated structure is a real file at any size
                yield Finding(start, result.end, sig, True, result.meta)
                consumed = start + result.end
            elif result.end >= sig.min_size:
                yield Finding(start, result.end, sig, False, result.meta)
        pos += chunk_size
        if on_progress:
            on_progress(min(pos, total), total)
