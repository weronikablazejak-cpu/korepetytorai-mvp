from fastapi import APIRouter
from app.db import SessionLocal
from app.models import User

router = APIRouter()

@router.get("/leaderboard")
def leaderboard(limit: int = 10):
    db = SessionLocal()

    users = (
        db.query(User)
        .order_by(User.xp.desc())
        .limit(limit)
        .all()
    )

    db.close()

    return [
        {
            "id": u.id,
            "name": u.name,
            "xp": u.xp,
            "level": u.level
        }
        for u in users
    ]
