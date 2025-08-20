from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from .models import * # noqa: F401
from .routers import auth_routes, chat_routes, admin_routes
from .logging_utils import app_logger
from .config import settings
from .bootstrap_admin import run as bootstrap_admin 

log = app_logger()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Librarian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(admin_routes.router) #fallback for admin routes - this is not a public API - used only for local development with admin secretkey


@app.get("/")
async def root():
    return {"status": "ok", "service": "smart-librarian"}

from .rag import count_books
@app.on_event("startup")
async def _log_counts():
    try:
        c = count_books()
        log.info(f"Chroma books count: {c}")
        bootstrap_admin()
    except Exception:
        log.warning("Could not count Chroma collection.")