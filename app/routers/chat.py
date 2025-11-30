from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta

from openai import OpenAI

from app.db import SessionLocal
from app.models import ChatMessage, Student, Conversation
from app.auth import get_current_user
from app.config import OPENAI_API_KEY

router = APIRouter()


class ChatIn(BaseModel):
    message: str


def get_or_create_conversation(db: Session, user: Student):
    convo = db.query(Conversation).filter_by(student_id=user.id).first()
    if not convo:
        convo = Conversation(student_id=user.id, created_at=datetime.utcnow())
        db.add(convo)
        db.commit()
        db.refresh(convo)
    return convo


def update_xp_and_level(user: Student, db: Session):
    user.xp += 5  # 5 XP za wiadomość

    # level = każde 100 XP
    user.level = user.xp // 100 + 1

    db.commit()
    db.refresh(user)


def update_streak(user: Student, db: Session):
    today = date.today()

    if not user.last_active:
        user.streak = 1
    else:
        last = user.last_active.date()
        if last == today:
            pass  # streak unchanged
        elif last == today - timedelta(days=1):
            user.streak += 1
        else:
            user.streak = 1

    user.last_active = datetime.utcnow()
    db.commit()
    db.refresh(user)


@router.post("/chat")
def chat(in_: ChatIn, user: Student = Depends(get_current_user)):
    db: Session = SessionLocal()

    # 🔥 1) Pobierz lub utwórz konwersację
    convo = get_or_create_conversation(db, user)

    # 🔥 2) Zapisz wiadomość użytkownika
    user_msg = ChatMessage(
        student_id=user.id,
        conversation_id=convo.id,
        role="user",
        content=in_.message
    )
    db.add(user_msg)
    db.commit()

    # 🔥 3) Pobierz historię ostatnich 20 wiadomości
    history = (
        db.query(ChatMessage)
        .filter_by(conversation_id=convo.id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(20)
        .all()
    )

    formatted_history = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history)
    ]

    # 🔥 4) Wywołanie OpenAI (NOWE API!)
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.responses.create(
            model="gpt-4o-mini",
            input=formatted_history + [{"role": "user", "content": in_.message}]
        )

        reply = response.output_text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    # 🔥 5) Zapisz odpowiedź AI
    ai_msg = ChatMessage(
        student_id=user.id,
        conversation_id=convo.id,
        role="assistant",
        content=reply
    )
    db.add(ai_msg)
    db.commit()

    # 🔥 6) XP + LEVEL + STREAK
    update_xp_and_level(user, db)
    update_streak(user, db)

    db.close()

    return {
        "answer": reply,
        "xp": user.xp,
        "level": user.level,
        "streak": user.streak
    }
