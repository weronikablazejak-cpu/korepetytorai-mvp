from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine
from app.models import Base
from app.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.leaderboard import router as leaderboard_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="KorepetytorAI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router)
app.include_router(leaderboard_router)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
