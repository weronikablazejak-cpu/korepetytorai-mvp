from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import SessionLocal
from app.models import User

router = APIRouter()

class AddXP(BaseModel):
    user_id: int
    xp: int


@router.post("/add_xp")
def add_xp(payload: AddXP):
    db = SessionLocal()

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        db.close()
        raise HTTPException(404, "Nie znaleziono użytkownika")

    user.xp += payload.xp

    # poziomy: co 100 XP = level up
    user.level = max(1, user.xp // 100 + 1)

    db.commit()
    db.refresh(user)
    db.close()

    return {
        "status": "ok",
        "user_id": user.id,
        "new_xp": user.xp,
        "level": user.level
    }
