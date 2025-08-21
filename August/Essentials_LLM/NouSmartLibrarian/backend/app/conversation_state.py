# backend/app/conversation_state.py
import json, time
from typing import Dict
from redis import Redis
from .config import settings

# încercăm Redis; dacă nu merge, avem fallback in-memory cu TTL
try:
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=0.3,
        socket_timeout=0.3,
    )
    redis.ping()
    _use_redis = True
except Exception:
    _use_redis = False
    _mem: Dict[str, tuple[dict, int]] = {}

TTL = 1800  # 30 min


def _now() -> int:
    return int(time.time())


def _key(sid: str) -> str:
    return f"ctx:{sid}"


def get_ctx(sid: str) -> dict:
    if _use_redis:
        raw = redis.get(_key(sid))
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {}
    rec = _mem.get(sid)
    if not rec:
        return {}
    data, exp = rec
    if _now() > exp:
        _mem.pop(sid, None)
        return {}
    return data


def update_ctx(sid: str, **kwargs) -> dict:
    cur = get_ctx(sid)
    cur.update({k: v for k, v in kwargs.items() if v is not None})
    if _use_redis:
        redis.setex(_key(sid), TTL, json.dumps(cur, ensure_ascii=False))
    else:
        _mem[sid] = (cur, _now() + TTL)
    return cur
