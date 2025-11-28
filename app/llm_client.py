# app/llm_client.py

from openai import OpenAI
import os

def get_llm_client() -> OpenAI:
    """
    Zwraca prawdziwego klienta OpenAI.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Brak zmiennej OPENAI_API_KEY!")

    return OpenAI(api_key=api_key)
