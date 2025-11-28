from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date

from app.db import SessionLocal
from app.models import Student, ChatMessage, UserStreak

router = APIRouter()


# -------------------------
# MODELE Pydantic
# -------------------------
class UserCreate(BaseModel):
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    xp: int
    level: int


class XPUpdate(BaseModel):
    xp: int


class MessageOut(BaseModel):
    role: str
    content: str


class ChatHistoryOut(BaseModel):
    user_id: int
    messages: List[MessageOut]


# =========================
# 1. TWORZENIE UCZNIA
# =========================
@router.post("/create", response_model=UserOut)
def create_user(payload: UserCreate):
    db = SessionLocal()

    student = Student(name=payload.name)
    db.add(student)
    db.commit()
    db.refresh(student)
    db.close()

    return UserOut(
        id=student.id,
        name=student.name,
        xp=student.xp,
        level=student.level
    )


# =========================
# 2. POBIERANIE STANU UCZNIA
# =========================
@router.get("/state/{user_id}", response_model=UserOut)
def get_user_state(user_id: int):
    db = SessionLocal()
    student = db.query(Student).filter(Student.id == user_id).first()
    db.close()

    if not student:
        raise HTTPException(404, "Nie znaleziono użytkownika")

    return UserOut(
        id=student.id,
        name=student.name,
        xp=student.xp,
        level=student.level
    )


# =========================
# 3. HISTORIA CZATU
# =========================
@router.get("/history/{user_id}", response_model=ChatHistoryOut)
def get_history(user_id: int):
    db = SessionLocal()

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    db.close()

    return ChatHistoryOut(
        user_id=user_id,
        messages=[MessageOut(role=m.role, content=m.content) for m in messages]
    )


# =========================
# 4. DODAWANIE XP
# =========================
@router.post("/{user_id}/add_xp", response_model=UserOut)
def add_xp(user_id: int, payload: XPUpdate):
    db = SessionLocal()

    student = db.query(Student).filter(Student.id == user_id).first()
    if not student:
        db.close()
        raise HTTPException(404, "Nie znaleziono użytkownika")

    student.xp += payload.xp

    # mechanika levelowania
    while student.xp >= student.level * 100:
        student.level += 1

    db.commit()
    db.refresh(student)
    db.close()

    return UserOut(
        id=student.id,
        name=student.name,
        xp=student.xp,
        level=student.level
    )


# =========================
# 5. LEADERBOARD
# =========================
@router.get("/leaderboard", response_model=List[UserOut])
def leaderboard():
    db = SessionLocal()

    students = (
        db.query(Student)
        .order_by(Student.xp.desc())
        .limit(50)
        .all()
    )

    db.close()

    return [
        UserOut(
            id=s.id,
            name=s.name,
            xp=s.xp,
            level=s.level
        )
        for s in students
    ]


# ===============================
# 6. STREAK API
# ===============================
class StreakResponse(BaseModel):
    user_id: int
    current_streak: int
    longest_streak: int
    last_streak_date: date | None


@router.get("/streak", response_model=StreakResponse)
def get_streak(user_id: int):
    db = SessionLocal()

    student = db.query(Student).filter(Student.id == user_id).first()
    if not student:
        db.close()
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    streak = (
        db.query(UserStreak)
        .filter(UserStreak.user_id == user_id)
        .first()
    )

    if not streak:
        db.close()
        return StreakResponse(
            user_id=user_id,
            current_streak=0,
            longest_streak=0,
            last_streak_date=None
        )

    response = StreakResponse(
        user_id=user_id,
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        last_streak_date=streak.last_streak_date
    )

    db.close()
    return response
