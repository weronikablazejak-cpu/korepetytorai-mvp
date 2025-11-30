from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# -----------------------------
# Rejestracja / Logowanie
# -----------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student_id: int
    name: str
    email: EmailStr
    xp: int
    level: int
    streak: int
    is_tester: bool
    is_active: bool
    subscription_expires: Optional[str]


# -----------------------------
# Wiadomości czatu
# -----------------------------
class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    answer: str
    xp_awarded: int
    total_xp: int
    level: int
    streak: int
    new_badges: List[str]
