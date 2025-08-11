import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import uuid

# Import passlib for password hashing
from passlib.context import CryptContext

Base = declarative_base()
engine = create_engine("sqlite:///app_data.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

load_dotenv()

DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL")
DEFAULT_PWD = os.getenv("DEFAULT_PWD")

# Configure hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "user"
    userID = Column(String, primary_key=True,
                    default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, unique=True)
    _password = Column("password", String, nullable=False)
    role = Column(String, default="")
    experience = Column(String, default="")
    seniority = Column(String, default="")

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, plain_password: str):
        self._password = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self._password)

class RequestLog(Base):
    __tablename__ = "requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create tables in a database if not exists"""
    Base.metadata.create_all(bind=engine)


def loadDefaultUser():
    """ Create default user in a database with hashed password """
    db = SessionLocal()
    user = db.query(User).filter_by(email=DEFAULT_EMAIL).first()
    if not user:
        new_user = User(
            email=DEFAULT_EMAIL,
            password=DEFAULT_PWD,
        )
        db.add(new_user)
        db.commit()
        print("Default user initialized", new_user.userID)
    else:
        print("Default user already existing", user.userID)
    db.close()