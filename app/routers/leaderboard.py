from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Student

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("")
def leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    students = (
        db.query(Student)
        .order_by(Student.xp.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": s.id,
            "name": s.name,
            "xp": s.xp,
            "level": s.level,
        }
        for s in students
    ]
