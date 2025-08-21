
from __future__ import annotations
from typing import List, Dict
import importlib

def retrieve_filtered(query: str, allowed_titles: List[str], k: int = 5) -> List[Dict]:
    try:
        rag = importlib.import_module("app.rag")
        retrieve = getattr(rag, "retrieve")
        res = retrieve(query, k=k) or []
    except Exception:
        try:
            rag = importlib.import_module("..rag", package=__package__)
            retrieve = getattr(rag, "retrieve")
            res = retrieve(query, k=k) or []
        except Exception:
            res = []

    out = []
    seen = set()
    for r in res:
        t = (r.get("title") or "").strip()
        if not t: continue
        if t in seen: continue
        if allowed_titles and t not in allowed_titles: continue
        seen.add(t); out.append(r)
        if len(out) >= k: break
    return out
