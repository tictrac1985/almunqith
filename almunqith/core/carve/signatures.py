"""Registry of carveable file signatures."""
from dataclasses import dataclass
from typing import Callable

from almunqith.core.carve.validators.jpeg import ValidationResult, validate_jpeg
from almunqith.core.carve.validators.png import validate_png
from almunqith.core.carve.validators.riff import validate_riff
from almunqith.core.carve.validators.mp4 import validate_mp4
from almunqith.core.carve.validators.images2 import (
    validate_gif, validate_bmp, validate_tiff)
from almunqith.core.carve.validators.docs import (
    validate_pdf, validate_zip, validate_ole2, validate_psd,
    validate_rar, validate_7z)
from almunqith.core.carve.validators.audio import (
    validate_mp3, validate_flac, validate_ogg)
from almunqith.core.carve.validators.video2 import validate_mkv, validate_asf

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


def _wav(data):                       # WAV = RIFF with WAVE variant
    r = validate_riff(data)
    if r.meta.get("variant") == "wave":
        return r
    return ValidationResult(0, False, {})


REGISTRY: tuple[Signature, ...] = (
    # ---- photos ----
    Signature("jpeg", "photos", ".jpg", (b"\xff\xd8\xff",), 0, validate_jpeg, 2048),
    Signature("png", "photos", ".png", (b"\x89PNG\r\n\x1a\n",), 0, validate_png, 256),
    Signature("gif", "photos", ".gif", (b"GIF87a", b"GIF89a"), 0, validate_gif, 64),
    Signature("bmp", "photos", ".bmp", (b"BM",), 0, validate_bmp, 128),
    Signature("tiff", "photos", ".tiff", (b"II*\x00", b"MM\x00*"), 0, validate_tiff, 256),
    Signature("psd", "photos", ".psd", (b"8BPS",), 0, validate_psd, 256),
    # HEIC / RAW share ISO-BMFF / TIFF walkers
    Signature("heic", "photos", ".heic", (b"ftyp",), 4, validate_mp4, 4096),
    Signature("cr2", "photos", ".cr2", (b"II*\x00",), 0, validate_tiff, 4096),
    # ---- videos ----
    Signature("avi", "videos", ".avi", (b"RIFF",), 0, validate_riff, 8192),
    Signature("mp4", "videos", ".mp4", (b"ftyp",), 4, validate_mp4, 8192),
    Signature("mkv", "videos", ".mkv", (b"\x1a\x45\xdf\xa3",), 0, validate_mkv, 8192),
    Signature("asf", "videos", ".wmv",
              (b"\x30\x26\xb2\x75\x8e\x66\xcf\x11",), 0, validate_asf, 8192),
    # ---- audio ----
    Signature("mp3", "audio", ".mp3", (b"ID3", b"\xff\xfb", b"\xff\xf3",
                                       b"\xff\xf2"), 0, validate_mp3, 512),
    Signature("wav", "audio", ".wav", (b"RIFF",), 0, _wav, 256),
    Signature("flac", "audio", ".flac", (b"fLaC",), 0, validate_flac, 256),
    Signature("ogg", "audio", ".ogg", (b"OggS",), 0, validate_ogg, 128),
    # ---- documents ----
    Signature("pdf", "documents", ".pdf", (b"%PDF-",), 0, validate_pdf, 256),
    Signature("ooxml", "documents", ".zip", (b"PK\x03\x04",), 0, validate_zip, 256),
    Signature("ole2", "documents", ".doc",
              (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",), 0, validate_ole2, 512),
    # ---- archives ----
    Signature("rar", "archives", ".rar", (b"Rar!\x1a\x07",), 0, validate_rar, 128),
    Signature("sevenz", "archives", ".7z", (b"7z\xbc\xaf\x27\x1c",), 0, validate_7z, 128),
    Signature("zip", "archives", ".zip", (b"PK\x03\x04",), 0, validate_zip, 256),
)


def for_categories(categories: set[str]) -> tuple[Signature, ...]:
    if "all" in categories:
        return REGISTRY
    return tuple(s for s in REGISTRY if s.category in categories)


def _noop(data: bytes) -> ValidationResult:      # never used to validate
    return ValidationResult(len(data), True, {})


GENERIC = Signature("file", "other", "", (), 0, _noop, 0)

_EXT_CATEGORY = {
    ".jpg": "photos", ".jpeg": "photos", ".png": "photos", ".gif": "photos",
    ".bmp": "photos", ".tif": "photos", ".tiff": "photos", ".heic": "photos",
    ".cr2": "photos", ".nef": "photos", ".arw": "photos", ".psd": "photos",
    ".mp4": "videos", ".mov": "videos", ".avi": "videos", ".mkv": "videos",
    ".wmv": "videos", ".3gp": "videos", ".m4v": "videos", ".webm": "videos",
    ".mp3": "audio", ".wav": "audio", ".flac": "audio", ".ogg": "audio",
    ".aac": "audio", ".m4a": "audio", ".wma": "audio",
    ".pdf": "documents", ".doc": "documents", ".docx": "documents",
    ".xls": "documents", ".xlsx": "documents", ".ppt": "documents",
    ".pptx": "documents", ".txt": "documents",
    ".zip": "archives", ".rar": "archives", ".7z": "archives",
}


def signature_for_name(filename: str) -> Signature:
    """A synthetic Signature for a filesystem-recovered file, categorized by
    its extension so the extractor files it under the right folder."""
    import os
    ext = os.path.splitext(filename)[1].lower()
    category = _EXT_CATEGORY.get(ext, "other")
    return Signature("file", category, ext, (), 0, _noop, 0)
