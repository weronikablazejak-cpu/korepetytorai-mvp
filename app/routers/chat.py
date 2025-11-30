from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import ChatMessage, Student
from app.auth import get_current_user
from app.config import OPENAI_API_KEY
import openai


router = APIRouter()


class ChatIn(BaseModel):
    message: str


@router.post("/chat")
def chat(in_: ChatIn, user: Student = Depends(get_current_user)):
    db: Session = SessionLocal()

    # Zapisujemy wiadomość użytkownika
    db.add(ChatMessage(student_id=user.id, role="user", content=in_.message))
    db.commit()

    # 🔥 ChatGPT odpowiedź
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": in_.message}
            ],
            max_tokens=250
        )

        reply = response.choices[0].message["content"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {e}")

    # Zapisujemy odpowiedź AI
    db.add(ChatMessage(student_id=user.id, role="assistant", content=reply))
    db.commit()
    db.close()

    return {"answer": reply}
