from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from app.models import ChatMessage, Student
from app.db import SessionLocal
from app.streak import update_streak_after_message
from app.auth import get_current_user
from app.config import OPENAI_API_KEY

from openai import OpenAI  # <-- NOWY POPRAWNY IMPORT


router = APIRouter()

def get_client():
    return OpenAI(api_key=OPENAI_API_KEY)


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    answer: str
    xp_awarded: int
    total_xp: int
    level: int
    streak: int
    new_badges: List[str]


@router.post("/chat", response_model=ChatOut)
def chat(in_: ChatIn, user=Depends(get_current_user)):

    if not in_.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    db = SessionLocal()

    # Pobranie studenta
    student = db.query(Student).filter(Student.id == user.id).first()
    if not student:
        db.close()
        raise HTTPException(status_code=404, detail="Student not found")

    # Zapis wiadomości użytkownika
    db.add(ChatMessage(
        student_id=student.id,
        role="user",
        content=in_.message
    ))
    db.commit()

    # OpenAI client
    client = get_client()

    # NOWY POPRAWNY FORMAT OPENAI API
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Jesteś KorepetytorAI."},
            {"role": "user", "content": in_.message}
        ]
    )

    answer = response.choices[0].message.content

    # Zapis odpowiedzi AI
    db.add(ChatMessage(
        student_id=student.id,
        role="assistant",
        content=answer
    ))

    # XP i leveling
    base_xp = 5
    bonus = 5 if len(in_.message) > 80 else 0
    xp_awarded = base_xp + bonus
    student.xp += xp_awarded

    while student.xp >= student.level * 100:
        student.level += 1

    streak = update_streak_after_message(db, student.id)

    db.commit()
    db.refresh(student)
    db.close()

    return ChatOut(
        answer=answer,
        xp_awarded=xp_awarded,
        total_xp=student.xp,
        level=student.level,
        streak=streak,
        new_badges=[]
    )
