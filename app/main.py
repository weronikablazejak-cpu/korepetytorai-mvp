from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.routers import (
    user,
    auth,
    chat,
    leaderboard,
    materials,
    xp,
    health
)

# --- CREATE TABLES ---
Base.metadata.create_all(bind=engine)

# --- APP INSTANCE ---
app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(auth. router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])
app.include_router(materials.router, prefix="/materials", tags=["Materials"])
app.include_router(xp.router, prefix="/xp", tags=["XP"])
app.include_router(health.router, prefix="/health", tags=["Health"])

# --- ROOT ---
@app.get("/")
def root():
    return {"status": "ok", "message": "KorepetytorAI backend running"}
