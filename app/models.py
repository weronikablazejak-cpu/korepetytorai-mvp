from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)

    is_tester = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    subscription_expires = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="student")
    streak = relationship("UserStreak", uselist=False, back_populates="student")
    conversation = relationship("Conversation", uselist=False, back_populates="student")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="conversation")
    messages = relationship("ChatMessage", back_populates="conversation")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))

    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")


class UserStreak(Base):
    __tablename__ = "user_streaks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))

    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_streak_date = Column(Date, nullable=True)

    student = relationship("Student", back_populates="streak")
