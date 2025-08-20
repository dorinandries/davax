from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError
from ._helpers import set_auth_cookies, clear_auth_cookies, get_current_user_optional
from ..schemas import RegisterStep2, LoginRequest, PrefsUpdate
from ..models import User, Preference
from ..db import get_db
from ..security import hash_password, verify_password, create_token, create_access_token, create_refresh_token
from ..otp import (
    generate_and_store_otp, verify_otp, can_send_otp, mark_otp_sent,
    generate_and_store_otp_reset, verify_otp_reset, can_send_otp_reset, mark_otp_sent_reset, invalidate_otp_reset
)
from ..config import settings
from ..email_service import send_otp_email
import re


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-otp")
async def send_otp(email: str):
    try:
        validate_email(email)
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not can_send_otp(email):
        raise HTTPException(status_code=429, detail="Too many requests. Try later.")
    code = generate_and_store_otp(email)
    send_otp_email(email, code)
    mark_otp_sent(email)
    return {"status": "ok"}


@router.post("/verify-otp")
async def verify(email: str, code: str):
    if verify_otp(email, code):
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Invalid code")


@router.post("/register")
async def register(payload: RegisterStep2, db: Session = Depends(get_db)):
    # minimă validare parolă: 8+ caractere, o literă, o cifră
    import re
    if not re.search(r"[A-Za-z]", payload.password) or not re.search(r"\d", payload.password):
        raise HTTPException(status_code=400, detail="Parolă slabă: trebuie litere și cifre.")

    if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="Email sau username deja folosit.")


    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role="user"  # implicit rolul este user
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"status": "ok"}


@router.post("/login")
async def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    u = db.query(User).filter((User.email == payload.identifier) | (User.username == payload.identifier)).first()
    if not u or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Credențiale invalide")

    access = create_access_token(u.id, u.role)
    refresh = create_refresh_token(u.id)

    set_auth_cookies(response, access, refresh)
    return {"status": "ok"}


@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    from ..security import decode_token
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="No refresh token")
    data = decode_token(refresh)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    u = db.get(User, data["sub"])  # sub = UUID
    if not u:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token(u.id, u.role)
    response.set_cookie("access_token", access, httponly=True, samesite="lax")
    return {"status": "ok"}


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"status": "ok"}


@router.get("/me")
async def me(user = Depends(get_current_user_optional)):
    return {"authenticated": bool(user), "user": user}


@router.post("/preferences")
async def set_prefs(payload: PrefsUpdate, user = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Auth required")
    db.query(Preference).filter(Preference.user_id == user["id"]).delete()
    for g in set(payload.genres):
        db.add(Preference(user_id=user["id"], genre=g))
    db.commit()
    return {"status": "ok"}

@router.post("/reset/send-otp")
async def reset_send_otp(email: str):
    # Răspuns generic pentru a evita user-enumeration
    try:
        validate_email(email)
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not can_send_otp_reset(email):
        raise HTTPException(status_code=429, detail="Too many requests. Try later.")
    code = generate_and_store_otp_reset(email)
    send_otp_email(email, code) # subiect generic din email_service
    mark_otp_sent_reset(email)
    return {"status": "ok"}


@router.post("/reset/verify")
async def reset_verify(email: str, code: str):
    if verify_otp_reset(email, code):
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Invalid code")


class ResetCompletePayload(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/reset/complete")
async def reset_complete(payload: ResetCompletePayload, db: Session = Depends(get_db)):
    # 1) Verifică OTP (fără a divulga dacă userul există)
    if not verify_otp_reset(payload.email, payload.code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    # 2) Validate password strength (8+, o majusculă, o cifră, un caracter special)
    pw = payload.new_password
    if not (len(pw) >= 8 and re.search(r"[A-Z]", pw) and re.search(r"\d", pw) and re.search(r"[^A-Za-z0-9]", pw)):
        raise HTTPException(status_code=400, detail="Parola trebuie să aibă min 8 caractere, o literă mare, o cifră și un caracter special.")


    # 3) Update user dacă există (răspunsul rămâne generic)
    u = db.query(User).filter(User.email == payload.email).first()
    if u:
        u.password_hash = hash_password(pw)
        db.add(u)
        db.commit()
    # 4) Invalidează OTP
    invalidate_otp_reset(payload.email)
    return {"status": "ok"}
