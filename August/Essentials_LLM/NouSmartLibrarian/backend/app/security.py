from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from jose import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(
    subject: str,
    token_type: str,
    expires_minutes: int | None = None,
    expires_days: int | None = None,
    extra_claims: Optional[Dict] = None,
) -> str:
    """
    subject: user.id (UUID string)
    token_type: "access" / "refresh"
    extra_claims: ex. {"role": "admin"}
    """
    now = datetime.now(timezone.utc)
    payload: Dict = {"sub": subject, "type": token_type, "iat": int(now.timestamp())}
    if expires_minutes:
        payload["exp"] = int((now + timedelta(minutes=expires_minutes)).timestamp())
    if expires_days:
        payload["exp"] = int((now + timedelta(days=expires_days)).timestamp())
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_access_token(user_id: str, role: str) -> str:
    return create_token(
        subject=user_id,
        token_type="access",
        expires_minutes=settings.access_minutes,
        extra_claims={"role": role},
    )


def create_refresh_token(user_id: str) -> str:
    return create_token(
        subject=user_id,
        token_type="refresh",
        expires_days=settings.refresh_days,
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except Exception:
        return None
