# backend/app/bootstrap_admin.py
import uuid
from sqlalchemy import or_
from .db import SessionLocal
from .models import User
from .security import hash_password
from .config import settings
from .logging_utils import app_logger

log = app_logger()

def run():
    if not settings.admin_bootstrap_enabled:
        return

    username = settings.admin_username.strip()
    email = settings.admin_email.strip()
    password = settings.admin_password

    if not username or not email or not password:
        log.warning("Admin bootstrap: lipsesc ADMIN_USERNAME/ADMIN_EMAIL/ADMIN_PASSWORD.")
        return

    with SessionLocal() as db:
        u = db.query(User).filter(or_(User.username == username, User.email == email)).first()

        if u is None:
            # creare user nou (id = UUID)
            u = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=hash_password(password),
                first_name="Admin",
                last_name="User",
                role="admin",
            )
            db.add(u)
            db.commit()
            log.info(f"Admin bootstrap: creat admin id={u.id} username={u.username} email={u.email}")
            return

        # deja există – opțional actualizăm
        changed = False
        if settings.admin_overwrite_password:
            u.password_hash = hash_password(password)
            changed = True
        if u.role != "admin":
            u.role = "admin"
            changed = True

        if changed:
            db.add(u)
            db.commit()
            log.info(f"Admin bootstrap: actualizat admin id={u.id} username={u.username}")
        else:
            log.info(f"Admin bootstrap: nimic de făcut (admin deja prezent: id={u.id})")
