from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from openai import OpenAI

from app.models import ChatMessage, Student
from app.db import SessionLocal
from app.streak import update_streak_after_message
from app.config import OPENAI_API_KEY

router = APIRouter()

client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================
# MODELE Pydantic
# ============================================
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


# ============================================
# ENDPOINT /chat
# ============================================
@router.post("/chat", response_model=ChatOut)
def chat(in_: ChatIn):

    if not in_.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    db = SessionLocal()

    # -------------------------------------------------
    # Pobierz studenta
    # -------------------------------------------------
    student = db.query(Student).filter(Student.id == in_.student_id).first()
    if not student:
        db.close()
        raise HTTPException(status_code=404, detail="Student not found")

    # -------------------------------------------------
    # Zapis wiadomości użytkownika
    # -------------------------------------------------
    msg_user = ChatMessage(
        student_id=student.id,
        role="user",
        content=in_.message
    )
    db.add(msg_user)
    db.commit()

    # -------------------------------------------------
    # GPT odpowiedź
    # -------------------------------------------------
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Jesteś KorepetytorAI."},
            {"role": "user", "content": in_.message}
        ]
    )

    answer = response.choices[0].message.content

    # -------------------------------------------------
    # Zapis odpowiedzi AI
    # -------------------------------------------------
    msg_ai = ChatMessage(
        student_id=student.id,
        role="assistant",
        content=answer
    )
    db.add(msg_ai)

    # -------------------------------------------------
    # XP (gamifikacja)
    # -------------------------------------------------
    base_xp = 5
    bonus = 5 if len(in_.message) > 80 else 0
    xp_awarded = base_xp + bonus

    student.xp += xp_awarded

    # levelowanie
    while student.xp >= student.level * 100:
        student.level += 1

    # -------------------------------------------------
    # streak
    # -------------------------------------------------
    streak = update_streak_after_message(db, student.id)

    db.commit()
    db.refresh(student)
    db.close()

    # -------------------------------------------------
    # odpowiedź API
    # -------------------------------------------------
    return ChatOut(
        answer=answer,
        xp_awarded=xp_awarded,
        total_xp=student.xp,
        level=student.level,
        streak=streak,
        new_badges=[]   # dodamy później, gdy dopniesz badges
    )
