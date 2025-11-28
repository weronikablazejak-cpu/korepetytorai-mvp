from openai import OpenAI
import os

def get_llm_client():
    """
    Zwraca klienta OpenAI z Twoim kluczem API.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Brak OPENAI_API_KEY w zmiennych środowiskowych.")

    client = OpenAI(api_key=api_key)
    return client
