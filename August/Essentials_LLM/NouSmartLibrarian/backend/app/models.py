from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey

from .db import Base
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True, unique=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Preference(Base):
    __tablename__ = "preferences"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    genre = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'genre', name='uq_user_genre'),)