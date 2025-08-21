
import re
from typing import List, Optional

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def clean_title_for_match(t: str) -> str:
    x = (t or "").strip().strip('"\''"”’“`")
    x = re.sub(r"\s*\(.*?\)\s*$", "", x)
    x = re.sub(r"\s*[:\-–—]\s*.*$", "", x)
    x = re.sub(r"\s+de\s+.+$", "", x, flags=re.I)
    return x

def match_title_key(title: str, keys: List[str]) -> Optional[str]:
    if not title:
        return None
    t = _norm(clean_title_for_match(title))
    for k in keys:
        if _norm(clean_title_for_match(k)) == t:
            return k
    for k in keys:
        if t and t in _norm(clean_title_for_match(k)):
            return k
    return None
