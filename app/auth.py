from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import schemas
from app.config import SECRET_KEY
from app.db import get_db
from app.models import Student

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def _require_secret_key() -> str:
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Secret key not configured",
        )
    return SECRET_KEY


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    secret = _require_secret_key()
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/register", response_model=schemas.LoginResponse)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(req.password)
    new_student = Student(
        name=req.name or "Uczeń",
        email=req.email,
        hashed_password=hashed,
        xp=0,
        level=1,
        is_tester=True,
        is_active=True,
        subscription_expires=None,
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    token = create_access_token({"sub": str(new_student.id)})

    return schemas.LoginResponse(
        access_token=token,
        student_id=new_student.id,
        name=new_student.name,
        email=new_student.email,
        xp=new_student.xp,
        level=new_student.level,
        streak=0,
        is_tester=bool(new_student.is_tester),
        is_active=bool(new_student.is_active),
        subscription_expires=new_student.subscription_expires,
    )


@router.post("/login", response_model=schemas.LoginResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == req.email).first()
    if not student or not verify_password(req.password, student.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(student.id)})

    return schemas.LoginResponse(
        access_token=token,
        student_id=student.id,
        name=student.name,
        email=student.email,
        xp=student.xp,
        level=student.level,
        streak=student.streak.current_streak if student.streak else 0,
        is_tester=bool(student.is_tester),
        is_active=bool(student.is_active),
        subscription_expires=student.subscription_expires,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Student:
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, _require_secret_key(), algorithms=[ALGORITHM])
        student_id = payload.get("sub")
        if student_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    student = db.query(Student).filter(Student.id == int(student_id)).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return student
