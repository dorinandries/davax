from redis import Redis, exceptions
from ..config import settings

ANON_USED = "anon:used:{sid}"
ANON_LIMIT = 3
ANON_TTL = 86400  # 24h

try:
    redis = Redis.from_url(settings.redis_url, decode_responses=True,
                           socket_connect_timeout=0.3, socket_timeout=0.3)
    redis.ping()
    _redis_ok = True
except Exception:
    _redis_ok = False
    _mem = {}

def anon_used_count(sid: str) -> int:
    if _redis_ok:
        try:
            val = redis.get(ANON_USED.format(sid=sid))
            return int(val or "0")
        except Exception:
            return 0
    return int(_mem.get(sid, 0))

def mark_anon_used(sid: str):
    if _redis_ok:
        try:
            key = ANON_USED.format(sid=sid)
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ANON_TTL)
            pipe.execute()
        except Exception:
            pass
    else:
        _mem[sid] = str(min(ANON_LIMIT, int(_mem.get(sid, "0")) + 1))
