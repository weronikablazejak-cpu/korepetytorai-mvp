# backend/app/routers/materials.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict

from rag.engine import rebuild_rag_all

router = APIRouter(prefix="/materials", tags=["Materials"])


class ActiveMaterial(BaseModel):
    filename: str


class BuildResponse(BaseModel):
    status: str
    knowledge: int
    tasks: int
    criteria: int


# Trzymamy nazwę "aktywnego" pliku tylko informacyjnie
_active_material: Optional[str] = None


@router.post("/active")
def set_active_material(material: ActiveMaterial):
    global _active_material
    _active_material = material.filename
    return {"active": _active_material}


@router.get("/active")
def get_active_material():
    return {"active": _active_material}


@router.post("/build", response_model=BuildResponse)
def build_rag():
    """
    Buduje całą bazę RAG ze wszystkich JSON-ów w rag/parsed.
    """
    stats: Dict[str, int] = rebuild_rag_all()
    return BuildResponse(status="ok", **stats)
