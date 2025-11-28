# app/routers/rag.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from openai import OpenAI

from rag.engine import query_rag
from app.routers import materials  # importujemy moduł, nie samą zmienną


router = APIRouter()


# ---------------------------------------------------------
# MODELE
# ---------------------------------------------------------
class RAGQueryIn(BaseModel):
    question: str


class RAGQueryOut(BaseModel):
    answer: str
    sources: List[str]


# ---------------------------------------------------------
# 📌 RAG QUERY – odpowiada na pytania ucznia w stylu Weroniki
# ---------------------------------------------------------
@router.post("/query", response_model=RAGQueryOut)
def rag_query(data: RAGQueryIn):
    """
    Odpowiada na pytania na podstawie aktualnie aktywnego materiału
    (ustawianego w /api/materials/activate).
    """

    # 🔹 pobieramy AKTUALNĄ wartość z modułu materials
    active_file = materials._active_material

    if not active_file:
        raise HTTPException(
            status_code=400,
            detail="Nie ustawiono aktywnego materiału."
        )

    # 1. Znajdź najlepsze fragmenty z bazy wektorowej
    top_chunks = query_rag(data.question)

    if not top_chunks:
        # nic sensownego nie znaleziono w materiale
        return RAGQueryOut(
            answer="Nie znalazłam w tym materiale odpowiedzi na to pytanie. "
                   "Spróbuj doprecyzować albo zapytaj o inny fragment.",
            sources=[]
        )

    context = "\n\n---\n\n".join(top_chunks)

    # 2. Przygotuj prompt dla modelu OpenAI
    system_msg = (
        "Jesteś korepetytorką z chemii o imieniu Weronika. "
        "Tłumaczysz prosto, po ludzku, jak na fajnych korepetycjach. "
        "Odpowiadasz TYLKO na podstawie podanych fragmentów materiału. "
        "Jeśli w materiale czegoś nie ma – mówisz wprost, że tego nie ma."
    )

    user_prompt = f"""
Pytanie ucznia:
{data.question}

Fragmenty materiału (notatki / arkusz / zasady):
{context}

Na podstawie tych fragmentów odpowiedz krok po kroku,
ale zwięźle i zrozumiale dla licealisty. Jeśli czegoś brakuje, powiedz to wprost.
"""

    client = OpenAI()  # klucz bierze z OPENAI_API_KEY ustawionego w systemie

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",  # możesz zmienić na inny, jeśli chcesz
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    answer_text = completion.choices[0].message.content.strip()

    return RAGQueryOut(
        answer=answer_text,
        sources=top_chunks,
    )
