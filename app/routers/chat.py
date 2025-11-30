from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import ChatMessage, Student
from app.db import get_db
from app.streak import update_streak_after_message
from app.auth import get_current_user
from app.config import OPENAI_API_KEY
from app.schemas import ChatIn, ChatOut

from openai import OpenAI

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY not configured",
        )
    return OpenAI(api_key=OPENAI_API_KEY)


@router.post("", response_model=ChatOut)
def chat(
    in_: ChatIn,
    authorization: str = Header(None),   # 🔥 kluczowe, żeby JWT działał
    db: Session = Depends(get_db),
):
    # 🔥 Pobranie usera z JWT
    user = get_current_user(authorization)

    if not in_.message or not in_.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    # 🔥 Pobieramy 20 ostatnich wiadomości użytkownika
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.student_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )

    formatted_history = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history)
    ]

    # Dodajemy wiadomość użytkownika
    formatted_history.append({"role": "user", "content": in_.message})

    # 🔥 Zapisujemy wiadomość użytkownika
    db.add(ChatMessage(
        student_id=user.id,
        role="user",
        content=in_.message,
        created_at=datetime.utcnow(),
    ))
    db.flush()

    # 🔥 Wywołanie OpenAI
    client = _get_client()

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=formatted_history,
        )
        answer = response.output_text
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    # 🔥 Zapisujemy odpowiedź AI
    db.add(ChatMessage(
        student_id=user.id,
        role="assistant",
        content=answer,
        created_at=datetime.utcnow(),
    ))

    # 🔥 XP system
    base_xp = 5
    bonus_xp = 5 if len(in_.message) > 80 else 0
    xp_awarded = base_xp + bonus_xp

    user.xp += xp_awarded

    while user.xp >= user.level * 100:
        user.level += 1

    # 🔥 Streak
    streak = update_streak_after_message(db, user.id)

    db.commit()
    db.refresh(user)

    return ChatOut(
        answer=answer,
        xp_awarded=xp_awarded,
        total_xp=user.xp,
        level=user.level,
        streak=streak,
        new_badges=[],
    )
