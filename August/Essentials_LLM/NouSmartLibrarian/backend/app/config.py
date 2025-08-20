from pydantic import BaseModel
import os

from dotenv import load_dotenv
load_dotenv()

class Settings(BaseModel):
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    env: str = os.getenv("ENV", "dev")

    admin_secret: str = os.getenv("ADMIN_SECRET", "change_me_admin")
    admin_bootstrap_enabled: bool = os.getenv("ADMIN_BOOTSTRAP_ENABLED", "false").lower() == "true"
    admin_username: str = os.getenv("ADMIN_USERNAME", "")
    admin_email: str = os.getenv("ADMIN_EMAIL", "")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")
    admin_overwrite_password: bool = os.getenv("ADMIN_OVERWRITE_PASSWORD", "false").lower() == "true"

    sqlite_url: str = os.getenv("SQLITE_URL", "sqlite:///./app.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_alg: str = os.getenv("JWT_ALG", "HS256")
    access_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    refresh_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_pass: str = os.getenv("SMTP_PASS", "")
    smtp_from: str = os.getenv("SMTP_FROM", "Smart Librarian <noreply@smartlib.test>")


    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    chat_model: str = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


    price_chat_input: float = float(os.getenv("PRICE_CHAT_INPUT", "0.0005"))
    price_chat_output: float = float(os.getenv("PRICE_CHAT_OUTPUT", "0.0015"))
    price_embedding: float = float(os.getenv("PRICE_EMBEDDING", "0.00002"))


    otp_ttl: int = int(os.getenv("OTP_TTL_SECONDS", "600"))
    otp_cooldown: int = int(os.getenv("OTP_SEND_COOLDOWN_SECONDS", "60"))
    otp_rate_limit_hour: int = int(os.getenv("OTP_RATE_LIMIT_PER_HOUR", "5"))


settings = Settings()