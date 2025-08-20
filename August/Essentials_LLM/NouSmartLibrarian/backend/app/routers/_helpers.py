from fastapi import Request, Response, HTTPException, Depends

from ..config import settings
from ..security import decode_token
from ..models import User
from ..db import get_db


def set_auth_cookies(response, access: str, refresh: str):
    access_max_age = settings.access_minutes * 60           # ex. 15 min
    refresh_max_age = settings.refresh_days * 86400         # ex. 7 zile
    cookie_kwargs = dict(
        httponly=True,
        samesite="lax",
        secure=(settings.env != "dev"),  # în prod -> True
    )
    response.set_cookie("access_token", access, max_age=access_max_age, **cookie_kwargs)
    response.set_cookie("refresh_token", refresh, max_age=refresh_max_age, **cookie_kwargs)

def clear_auth_cookies(response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def get_current_user_optional(request: Request, db = Depends(get_db)):
    token = request.cookies.get("access_token")
    data = decode_token(token) if token else None
    if not data or data.get("type") != "access":
        return None
    uid = data["sub"]  # UUID string
    u = db.get(User, uid)
    if not u:
        return None
    return {"id": u.id, "email": u.email, "username": u.username, "role": u.role, "first_name": u.first_name, "last_name": u.last_name}


def require_roles(*roles):
    def _dep(u: User | None = Depends(get_current_user_optional)):
        if not u or u.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return u
    return _dep