from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from redis import Redis
from ..config import settings
from ..db import get_db
from ..models import User, Preference
from ..chroma_setup import reset_collection
from ._helpers import require_roles
from ..rag import count_books, retrieve

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/clear")
async def clear_all(
    target: str = "all",
    admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),  # <— rolul admin este necesar
):
    # (optional) acceptă și cheie de service pe lângă rol — util pentru CI/dev
    if admin_secret and admin_secret == settings.admin_secret:
        pass  # ok by secret
    # dacă vrei STRICT rol, șterge blocul de mai sus și argumentul admin_secret

    cleared = []
    if target in ("users", "sqlite", "all"):
        db.query(User).delete(); cleared.append("users")
    if target in ("preferences", "sqlite", "all"):
        db.query(Preference).delete(); cleared.append("preferences")
    if any(t in target for t in ("sqlite", "all", "users", "preferences")):
        db.commit()
    if target in ("redis", "all"):
        r = Redis.from_url(settings.redis_url, decode_responses=True)
        for pat in ["anon:used:*","otp:*","otp:last_sent:*","otp:hour:*","otp_reset:*","otp_reset:last_sent:*","otp_reset:hour:*"]:
            for k in r.scan_iter(pat): r.delete(k)
        cleared.append("redis")
    if target in ("chroma", "all"):
        reset_collection(); cleared.append("chroma")
    return {"status": "ok", "cleared": cleared or [target]}

@router.get("/chroma-stats")
def chroma_stats():
    return {"count": count_books()}

@router.get("/chroma-sample")
def chroma_sample(q: str = "prietenie și magie", k: int = 2):
    return {"sample": retrieve(q, k)}