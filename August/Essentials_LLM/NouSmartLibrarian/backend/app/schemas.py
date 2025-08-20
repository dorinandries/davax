from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


class RegisterStep2(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8)
    first_name: str
    last_name: str


class LoginRequest(BaseModel):
    identifier: str # email sau username
    password: str


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    status: str
    message: str
    recommended_title: Optional[str] = None
    summary: Optional[str] = None


class PrefsUpdate(BaseModel):
    genres: List[str]