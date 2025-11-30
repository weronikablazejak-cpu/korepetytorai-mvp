from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

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
    db: Session = Depends(get_db),
    user: Student = Depends(get_current_user),
):
    if not in_.message or not in_.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    # Save user message
    db.add(ChatMessage(student_id=user.id, role="user", content=in_.message))
    db.flush()

    # Call OpenAI
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Jesteś KorepetytorAI."},
                {"role": "user", "content": in_.message},
            ],
        )
        answer = response.choices[0].message.content
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch response from OpenAI")

    # Save assistant reply
    db.add(ChatMessage(student_id=user.id, role="assistant", content=answer))

    # XP and leveling
    base_xp = 5
    bonus = 5 if len(in_.message) > 80 else 0
    xp_awarded = base_xp + bonus
    user.xp += xp_awarded

    while user.xp >= user.level * 100:
        user.level += 1

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
