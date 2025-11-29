import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
MATERIALS_DIR = BASE_DIR / "app" / "materials"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY nie jest ustawione w środowisku!")