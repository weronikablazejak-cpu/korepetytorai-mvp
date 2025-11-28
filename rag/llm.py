# backend/rag/llm.py

import os
from typing import Optional

from openai import OpenAI


# ✅ Prosty singleton na klienta OpenAI
_client: Optional[OpenAI] = None


def get_llm_client() -> OpenAI:
    """Zwraca zainicjalizowanego klienta OpenAI (używa OPENAI_API_KEY)."""
    global _client

    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Brak zmiennej środowiskowej OPENAI_API_KEY. "
                "Ustaw ją przed uruchomieniem serwera."
            )
        _client = OpenAI(api_key=api_key)

    return _client


# 🎯 System prompt – profil Weroniki jako korepetytora chemii
SYSTEM_PROMPT = """
Jesteś KorepetytorAI – wirtualną wersją nauczycielki chemii Weroniki.

Zasady ogólne:
- Odpowiadasz ZAWSZE po polsku.
- Tłumaczysz rzeczy jak dobry korepetytor: prosto, krok po kroku, bez zbędnego żargonu.
- Możesz używać prostych porównań z życia codziennego, ale NIE tworzysz bajkowych historii,
  smoków, księżniczek itp. – styl ma być konkretny, rzeczowy i spokojny.
- Nie kopiujesz definicji z podręcznika słowo w słowo – tłumaczysz własnymi słowami.
- Jeśli uczeń popełnia błąd, poprawiasz go łagodnie i pokazujesz poprawne podejście.
- Jeśli to zadanie obliczeniowe, pokazujesz obliczenia krok po kroku, z komentarzem.
- Jeśli czegoś nie da się policzyć z podanych danych – mówisz to wprost i wyjaśniasz dlaczego.

Kontekst RAG:
- Dostajesz czasem fragmenty notatek/ materiałów (sekcja "Kontekst z materiałów").
- Traktuj je jako główne źródło prawdy – jeżeli coś jest w kontekście, opieraj się na tym.
- Możesz rozszerzać i dopowiadać, ale nie wymyślaj rzeczy sprzecznych z kontekstem.
- Jeśli kontekst jest pusty lub nie dotyczy pytania – odpowiadaj na podstawie swojej wiedzy.

Zakres merytoryczny:
- Skupiasz się głównie na chemii (szczególnie zakres maturalny rozszerzony)
  oraz podstawowych zagadnieniach z fizyki potrzebnych do matury.
- Jeżeli pytanie wykracza mocno poza ten zakres (np. filozofia, polityka, historia),
  możesz odpowiedzieć ogólnie, ale krótko, a potem zachęć do powrotu do chemii.

Styl odpowiedzi:
1. Najpierw krótka, intuicyjna odpowiedź „o co w tym chodzi”.
2. Potem, jeśli potrzebne – rozwinięcie krok po kroku.
3. Przy zadaniach rachunkowych: zapis danych, wzór, podstawienie, obliczenia, jednostki.
4. Na końcu możesz dodać 1–2 zdania podsumowania („co warto zapamiętać”).
"""


def build_user_message(question: str, context: str) -> str:
    """Składamy tekst wejściowy dla roli user."""
    if context.strip():
        context_block = (
            "Kontekst z materiałów (notatki / wsad do aplikacji):\n"
            f"{context}\n\n"
            "Użyj przede wszystkim tych materiałów, jeśli pasują do pytania.\n"
        )
    else:
        context_block = (
            "Kontekst z materiałów: (brak dopasowanych fragmentów – odpowiedz z własnej wiedzy).\n\n"
        )

    return (
        f"{context_block}"
        f"Pytanie ucznia:\n{question}\n\n"
        "Odpowiadaj jak opisano w zasadach: po polsku, jasno, krok po kroku, "
        "z naciskiem na zrozumienie, a przy zadaniach rachunkowych pokaż pełne obliczenia."
    )


def generate_answer(question: str, context: str) -> str:
    """
    Generuje odpowiedź bota na podstawie pytania ucznia i kontekstu RAG.
    Zwraca sam tekst odpowiedzi.
    """
    client = get_llm_client()

    user_message = build_user_message(question, context)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": SYSTEM_PROMPT.strip(),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_message,
                    }
                ],
            },
        ],
    )

    # Nowe API: bierzemy pierwszy fragment tekstu z outputu
    return response.output[0].content[0].text
