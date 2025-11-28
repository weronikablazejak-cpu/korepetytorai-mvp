from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# -----------------------------
# Rejestracja / Logowanie
# -----------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    student_id: int
    name: str
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
    student_id: int
    message: str


class ChatOut(BaseModel):
    answer: str
    xp_awarded: int
    total_xp: int
    level: int
    streak: int
    new_badges: List[str]
