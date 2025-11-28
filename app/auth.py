from fastapi import APIRouter, HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime

from app.db import SessionLocal
from app.models import Student
from app.schemas import RegisterRequest, LoginRequest, LoginResponse

router = APIRouter()


# ---------------------------------------------------------
# REJESTRACJA
# ---------------------------------------------------------
@router.post("/register", response_model=LoginResponse)
def register(req: RegisterRequest):

    db = SessionLocal()

    # sprawdź czy email już istnieje
    student = db.query(Student).filter(Student.email == req.email).first()
    if student:
        db.close()
        raise HTTPException(status_code=400, detail="Email już istnieje.")

    hashed = generate_password_hash(req.password)

    # nowy student
    new_student = Student(
        name=req.name or "Uczeń",
        email=req.email,
        hashed_password=hashed,
        xp=0,
        level=1,
        is_tester=True,   # testerzy mają dostęp free
        is_active=True,
        subscription_expires=None
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    token = secrets.token_hex(20)

    db.close()

    return LoginResponse(
        token=token,
        student_id=new_student.id,
        name=new_student.name,
        xp=new_student.xp,
        level=new_student.level,
        streak=0,
        is_tester=True,
        is_active=True,
        subscription_expires=None
    )


# ---------------------------------------------------------
# LOGOWANIE
# ---------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):

    db = SessionLocal()

    student = db.query(Student).filter(Student.email == req.email).first()
    if not student:
        db.close()
        raise HTTPException(status_code=404, detail="Nie znaleziono konta.")

    if not check_password_hash(student.hashed_password, req.password):
        db.close()
        raise HTTPException(status_code=401, detail="Nieprawidłowe hasło.")

    token = secrets.token_hex(20)

    response = LoginResponse(
        token=token,
        student_id=student.id,
        name=student.name,
        xp=student.xp,
        level=student.level,
        streak=0,  # streak pobierasz osobnym endpointem
        is_tester=bool(student.is_tester),
        is_active=bool(student.is_active),
        subscription_expires=student.subscription_expires
    )

    db.close()
    return response
