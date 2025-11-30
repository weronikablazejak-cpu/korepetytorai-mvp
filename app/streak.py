from datetime import date
from sqlalchemy.orm import Session
from app.models import UserStreak


def update_streak_after_message(db: Session, student_id: int) -> int:
    """Update streak for a student based on today's activity."""
    today = date.today()

    streak = db.query(UserStreak).filter(UserStreak.student_id == student_id).first()
    if not streak:
        streak = UserStreak(
            student_id=student_id,
            current_streak=1,
            longest_streak=1,
            last_streak_date=today,
        )
        db.add(streak)
        db.flush()
        return streak.current_streak

    last_date = streak.last_streak_date

    if last_date == today:
        return streak.current_streak

    delta_days = (today - last_date).days if last_date else None

    if delta_days == 1:
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    streak.last_streak_date = today
    db.flush()

    return streak.current_streak
