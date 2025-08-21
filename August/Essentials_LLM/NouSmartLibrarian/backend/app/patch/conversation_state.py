
from __future__ import annotations
from typing import Dict, Any
import time

_STATE: Dict[str, Dict[str, Any]] = {}
_TTL = 3600

def _now(): return int(time.time())

def get_ctx(sid: str) -> Dict[str, Any]:
    o = _STATE.get(sid) or {}
    if o.get("_t", 0) + _TTL < _now():
        o = {}
    o["_t"] = _now()
    _STATE[sid] = o
    return o

def update_ctx(sid: str, **kwargs) -> Dict[str, Any]:
    ctx = get_ctx(sid)
    for k, v in kwargs.items():
        ctx[k] = v
    ctx["_t"] = _now()
    _STATE[sid] = ctx
    return ctx
