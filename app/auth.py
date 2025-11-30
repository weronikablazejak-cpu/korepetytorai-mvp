from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt

from app.db import SessionLocal
from app.models import Student
from app.config import SECRET_KEY

from passlib.context import CryptContext

# 🔥 Stabilny backend — argon2, działa idealnie na Railway
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h


# ----------------------------
# Schemas
# ----------------------------
class RegisterIn(BaseModel):
    email: str
    password: str
    name: str


class LoginIn(BaseModel):
    email: str
    password: str


# ----------------------------
# JWT helper
# ----------------------------
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ----------------------------
# Password helper
# ----------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ----------------------------
# Register
# ----------------------------
@router.post("/auth/register")
def register(data: RegisterIn):
    db: Session = SessionLocal()

    existing = db.query(Student).filter(Student.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(data.password)

    student = Student(
        email=data.email,
        hashed_password=hashed,
        name=data.name,
        xp=0,
        level=1,
        is_tester=True,
        is_active=True,
        subscription_expires=None,
    )

    db.add(student)
    db.commit()
    db.refresh(student)
    db.close()

    return {"message": "Account created!"}


# ----------------------------
# Login
# ----------------------------
@router.post("/auth/login")
def login(data: LoginIn):
    db: Session = SessionLocal()

    student = db.query(Student).filter(Student.email == data.email).first()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"id": student.id, "email": student.email})

    return {
        "token": token,
        "student_id": student.id,
        "name": student.name
    }


# ----------------------------
# Auth dependency (placeholder)
# ----------------------------
def get_current_user(token: str = Depends(lambda: None)):
    """To uzupełnimy później, jak dodamy subskrypcje."""
    return None
