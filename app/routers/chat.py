from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import ChatMessage, Student, Conversation
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


def get_or_create_conversation(db: Session, user: Student):
    convo = (
        db.query(Conversation)
        .filter(Conversation.student_id == user.id)
        .first()
    )
    if not convo:
        convo = Conversation(
            student_id=user.id,
            created_at=datetime.utcnow()
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)
    return convo


@router.post("", response_model=ChatOut)
def chat(
    in_: ChatIn,
    db: Session = Depends(get_db),
    user: Student = Depends(get_current_user),
):
    if not in_.message or not in_.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    # 🔥 1. Pobieramy konwersację
    convo = get_or_create_conversation(db, user)

    # 🔥 2. Pobieramy ostatnie 20 wiadomości tej konwersacji
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == convo.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )

    formatted_history = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history)
    ]

    # Dodaj wiadomość użytkownika
    formatted_history.append({"role": "user", "content": in_.message})

    # 🔥 3. Zapisujemy wiadomość usera
    db.add(ChatMessage(
        student_id=user.id,
        conversation_id=convo.id,
        role="user",
        content=in_.message
    ))
    db.flush()

    # 🔥 4. Wywołanie OpenAI w nowym API
    client = _get_client()

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=formatted_history
        )
        answer = response.output_text
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI error: {str(e)}"
        )

    # 🔥 5. Zapisujemy odpowiedź AI
    db.add(ChatMessage(
        student_id=user.id,
        conversation_id=convo.id,
        role="assistant",
        content=answer
    ))

    # 🔥 6. XP przy każdej wiadomości
    base_xp = 5
    bonus_xp = 5 if len(in_.message) > 80 else 0
    xp_awarded = base_xp + bonus_xp

    user.xp += xp_awarded

    # Level-up co 100 XP
    while user.xp >= user.level * 100:
        user.level += 1

    # 🔥 7. Aktualizacja streaka
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
