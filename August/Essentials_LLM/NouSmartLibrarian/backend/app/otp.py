import secrets, time
from datetime import datetime
from redis import Redis
from .config import settings


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
    # store local: email -> (code, exp_ts) / "reset:email" -> (code, exp_ts)
    _store = {}
    # cooldown: email -> exp_ts      / "reset:email" -> exp_ts
    _last_sent = {}
    # ratelimit orar: "email:YYYYMMDDHH" -> (count, exp_ts)
    _hour_count = {}

def _now() -> int:
    return int(time.time())

OTP_KEY = "otp:{email}"
OTP_LAST_SENT = "otp:last_sent:{email}"
OTP_HOURLY_COUNT = "otp:hour:{email}:{hour}"


# --- RESET PASSWORD NAMESPACE ---
RESET_OTP_KEY = "otp_reset:{email}"
RESET_OTP_LAST_SENT = "otp_reset:last_sent:{email}"
RESET_OTP_HOURLY_COUNT = "otp_reset:hour:{email}:{hour}"


def generate_and_store_otp(email: str) -> str:
    code = str(secrets.randbelow(900000) + 100000) # 6 cifre
    redis.setex(OTP_KEY.format(email=email), settings.otp_ttl, code)
    return code


def verify_otp(email: str, code: str) -> bool:
    stored = redis.get(OTP_KEY.format(email=email))
    return stored is not None and stored == code


def can_send_otp(email: str) -> bool:
    # cooldown
    if redis.exists(OTP_LAST_SENT.format(email=email)):
        return False
    # rate limit orar
    hour = datetime.utcnow().strftime('%Y%m%d%H')
    key = OTP_HOURLY_COUNT.format(email=email, hour=hour)
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 3600)
    return count <= settings.otp_rate_limit_hour


def mark_otp_sent(email: str):
    redis.setex(OTP_LAST_SENT.format(email=email), settings.otp_cooldown, "1")


def generate_and_store_otp_reset(email: str) -> str:
    code = str(secrets.randbelow(900000) + 100000)
    if _use_redis:
        redis.setex(RESET_OTP_KEY.format(email=email), settings.otp_ttl, code)
    else:
        _store["reset:"+email] = (code, _now() + settings.otp_ttl)
    return code


def verify_otp_reset(email: str, code: str) -> bool:
    if _use_redis:
        val = redis.get(RESET_OTP_KEY.format(email=email))
        return val is not None and val == code
    tup = _store.get("reset:"+email)
    return bool(tup) and tup[0] == code and _now() <= tup[1]


def can_send_otp_reset(email: str) -> bool:
    if _use_redis:
        if redis.exists(RESET_OTP_LAST_SENT.format(email=email)):
            return False
        from datetime import datetime
        hour = datetime.utcnow().strftime('%Y%m%d%H')
        key = RESET_OTP_HOURLY_COUNT.format(email=email, hour=hour)
        count = redis.incr(key)
        if count == 1:
            redis.expire(key, 3600)
        return count <= settings.otp_rate_limit_hour
    now = _now()
    if _last_sent.get("reset:"+email, 0) > now:
        return False
    from datetime import datetime
    hour = datetime.utcnow().strftime('%Y%m%d%H')
    k = f"reset:{email}:{hour}"
    cnt, exp = _hour_count.get(k, (0, now + 3600))
    if now > exp:
        cnt, exp = 0, now + 3600
    cnt += 1
    _hour_count[k] = (cnt, exp)
    return cnt <= settings.otp_rate_limit_hour


def mark_otp_sent_reset(email: str):
    if _use_redis:
        redis.setex(RESET_OTP_LAST_SENT.format(email=email), settings.otp_cooldown, "1")
    else:
        _last_sent["reset:"+email] = _now() + settings.otp_cooldown


def invalidate_otp_reset(email: str):
    if _use_redis:
        try:
            redis.delete(RESET_OTP_KEY.format(email=email))
        except Exception:
            pass
    else:
        _store.pop("reset:"+email, None)