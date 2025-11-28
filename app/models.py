from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base

# -----------------------------
# TABELA students
# -----------------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)

    is_tester = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    subscription_expires = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="student")
    streak = relationship("UserStreak", uselist=False, back_populates="student")


# -----------------------------
# TABELA messages
# -----------------------------
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="messages")


# -----------------------------
# TABELA streak
# -----------------------------
class UserStreak(Base):
    __tablename__ = "user_streaks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))

    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_streak_date = Column(Date, nullable=True)

    student = relationship("Student", back_populates="streak")
