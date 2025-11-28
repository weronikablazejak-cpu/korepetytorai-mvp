from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine
from app.models import Base

from app.auth import router as auth_router
from app.routers.chat import router as chat_router

# -------------------------------
# Tworzenie tabel (NOWE MODELE)
# -------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(
    title="KorepetytorAI Backend",
    version="1.0.0",
)

# -------------------------------
# CORS – na razie open access
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Routers
# -------------------------------
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

# -------------------------------
# Healthcheck
# -------------------------------
@app.get("/")
def root():
    return {"status": "ok"}
