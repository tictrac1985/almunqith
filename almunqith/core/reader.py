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
