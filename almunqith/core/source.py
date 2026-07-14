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
