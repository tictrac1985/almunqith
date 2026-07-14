"""Tiny i18n: JSON dictionaries, Arabic default, English fallback."""
import json
import os

_DIR = os.path.dirname(__file__)
_LANG = "ar"
_CACHE: dict[str, dict] = {}


def _load(code: str) -> dict:
    if code not in _CACHE:
        path = os.path.join(_DIR, f"strings_{code}.json")
        with open(path, encoding="utf-8") as f:
            _CACHE[code] = json.load(f)
    return _CACHE[code]


def set_language(code: str):
    global _LANG
    _LANG = code if code in ("ar", "en") else "en"


def get_language() -> str:
    return _LANG


def is_rtl() -> bool:
    return _LANG == "ar"


def tr(key: str, **fmt) -> str:
    text = _load(_LANG).get(key) or _load("en").get(key) or key
    return text.format(**fmt) if fmt else text
