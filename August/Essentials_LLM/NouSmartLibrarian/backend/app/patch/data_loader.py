
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import re, json, os

from .title_match import match_title_key

SEARCH_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "data",
    Path(__file__).resolve().parents[3] / "data",
    Path(__file__).resolve().parents[1] / "data",
    Path.cwd() / "backend" / "app" / "data",
    Path.cwd() / "backend" / "data",
    Path.cwd() / "data",
]

def _read_json(p: Path) -> Dict[str, str]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _read_md(p: Path) -> Dict[str, str]:
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        return {}
    out = {}
    items = re.split(r'^##\s*Title:\s*', txt, flags=re.M)
    for chunk in items:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        title = lines[0].strip()
        summary = "\n".join(lines[1:]).strip()
        if title:
            out[title] = summary
    return out

def load_summaries() -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    js, md = {}, {}
    for base in SEARCH_CANDIDATES:
        if not base.exists():
            continue
        pj = base / "book_summaries.json"
        pm = base / "book_summaries.md"
        if not js and pj.exists():
            js = _read_json(pj)
        if not md and pm.exists():
            md = _read_md(pm)
        if js or md:
            break
    keys = list(js.keys()) + [k for k in md.keys() if k not in js]
    return js, md, keys

BOOK_JSON, BOOK_MD, TITLE_KEYS = load_summaries()

def get_summary_by_title(title: str) -> str:
    k = match_title_key(title, TITLE_KEYS)
    if k is None:
        return "Rezumat indisponibil pentru acest titlu."
    if k in BOOK_JSON:
        s = BOOK_JSON.get(k) or ""
        return s if s.strip() else "Rezumat indisponibil pentru acest titlu."
    if k in BOOK_MD:
        s = BOOK_MD.get(k) or ""
        return s if s.strip() else "Rezumat indisponibil pentru acest titlu."
    return "Rezumat indisponibil pentru acest titlu."
