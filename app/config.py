import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MATERIALS_DIR = BASE_DIR / "app" / "materials"

# Jak chcesz, możesz dalej używać OpenAI z ENV
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔑 SECRET_KEY – albo z ENV, albo stały fallback
SECRET_KEY = os.getenv("SECRET_KEY") or "korepetytorai_dev_secret_weronika_2025"
