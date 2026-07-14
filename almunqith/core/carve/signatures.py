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
