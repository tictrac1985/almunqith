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
