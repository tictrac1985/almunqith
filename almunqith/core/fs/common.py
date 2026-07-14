"""Shared types for filesystem-aware undelete."""
from dataclasses import dataclass


@dataclass
class RecoveredEntry:
    """A deleted file recovered from surviving filesystem metadata."""
    name: str
    size: int
    first_offset: int          # absolute byte offset of the file data
    mtime: str                 # ISO-ish "YYYY-MM-DD HH:MM:SS" or ""
    contiguous: bool           # True when data is assumed unfragmented
    fs: str                    # "fat", "exfat", "ntfs"
