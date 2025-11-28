from datetime import date
from sqlalchemy.orm import Session
from app.models import Student

def update_streak_after_message(db: Session, student_id: int) -> int:
    """
    Aktualizuje streak ucznia po wiadomości.
    Zwraca: current_streak (int)
    """
    today = date.today()

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return 0

    last_date = student.last_streak_date

    # 1) brak daty -> pierwszy dzień
    if last_date is None:
        student.current_streak = 1
        student.longest_streak = 1
        student.last_streak_date = today
        db.commit()
        return student.current_streak

    # 2) dzisiaj już był streak — nic nie rób
    if last_date == today:
        return student.current_streak

    # 3) wczoraj było -> +1
    delta_days = (today - last_date).days

    if delta_days == 1:
        student.current_streak += 1
    else:
        # przerwa -> reset
        student.current_streak = 1

    # longest streak
    if student.current_streak > student.longest_streak:
        student.longest_streak = student.current_streak

    student.last_streak_date = today
    db.commit()

    return student.current_streak
