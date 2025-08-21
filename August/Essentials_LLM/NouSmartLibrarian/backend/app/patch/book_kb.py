
from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any
import json

from .data_loader import TITLE_KEYS
from .title_match import match_title_key

# Optional metadata store
CANDIDATE_PATHS = [
    Path(__file__).resolve().parents[2] / "data" / "book_metadata.json",
    Path(__file__).resolve().parents[3] / "data" / "book_metadata.json",
    Path(__file__).resolve().parents[1] / "data" / "book_metadata.json",
    Path.cwd() / "backend" / "app" / "data" / "book_metadata.json",
    Path.cwd() / "backend" / "data" / "book_metadata.json",
    Path.cwd() / "data" / "book_metadata.json",
]

def _load_meta() -> Dict[str, Any]:
    for p in CANDIDATE_PATHS:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
    return {}

META = _load_meta()

def _get_field(title: str, field: str):
    k = match_title_key(title, list(META.keys()) or TITLE_KEYS)
    if not k: return None
    v = META.get(k, {}).get(field)
    return v

def get_pages(title: str) -> Optional[int]:
    v = _get_field(title, "pages")
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

def get_author(title: str) -> Optional[str]:
    v = _get_field(title, "author")
    return v

def get_year(title: str) -> Optional[int]:
    v = _get_field(title, "year")
    try:
        return int(v) if v is not None else None
    except Exception:
        return None
