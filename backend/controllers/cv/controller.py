import json
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.cv.extractor import (
    cv_exists,
    profile_exists,
    get_profile,
    extract_profile,
    CV_PATH,
    PROFILE_PATH,
)
from services.search.config import populate_from_profile
from models.profile import Profile

ROOT = Path(__file__).parent.parent.parent

router = APIRouter()


class ProfileUpdate(BaseModel):
    nombre: Optional[str] = None
    cargo_objetivo: Optional[list[str]] = None
    skills: Optional[list[str]] = None
    educacion: Optional[str] = None
    experiencia_anos: Optional[int] = None
    idiomas: Optional[list[str]] = None
    resumen: Optional[str] = None
    ubicacion: Optional[str] = None
    graduado: Optional[bool] = None
    ano_graduacion: Optional[int] = None
    sobre_mi: Optional[str] = None


@router.get("/cv/status")
def get_cv_status():
    profile = get_profile()
    return {
        "cv_uploaded": cv_exists(),
        "profile_extracted": profile_exists(),
        "profile": profile.model_dump() if profile else None,
    }


@router.post("/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(400, "El archivo debe ser un PDF")

    CV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CV_PATH.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Si ya había un perfil extraído, lo borramos para forzar re-extracción
    profile_path = ROOT / "data" / "state" / "profile.json"
    if profile_path.exists():
        profile_path.unlink()

    return {"ok": True}


@router.patch("/cv/profile")
def update_profile(body: ProfileUpdate):
    profile = get_profile()
    if not profile:
        raise HTTPException(400, "No hay perfil extraído aún")
    data = profile.model_dump()
    patch = body.model_dump(exclude_none=True)
    data.update(patch)
    updated = Profile(**data)
    PROFILE_PATH.write_text(updated.model_dump_json(indent=2), encoding="utf-8")
    populate_from_profile(updated.cargo_objetivo, updated.ubicacion)
    # Borra scores_meta para que el frontend detecte scores obsoletos
    scores_meta = ROOT / "data" / "state" / "scores_meta.json"
    if scores_meta.exists():
        scores_meta.unlink()
    return {"ok": True, "profile": updated.model_dump()}


@router.post("/cv/suggest-roles")
def suggest_roles():
    profile = get_profile()
    if not profile:
        raise HTTPException(400, "No hay perfil extraído aún")
    if not profile.sobre_mi:
        raise HTTPException(400, "Escribe algo en 'Sobre mí' primero")

    from services.llm.client import chat_json, _load_config
    cfg = _load_config()
    prompt = f"""El candidato tiene estos cargos objetivo actualmente: {", ".join(profile.cargo_objetivo)}

El candidato dice sobre sí mismo:
{profile.sobre_mi}

Basándote en lo que dice, sugiere entre 2 y 5 roles adicionales que podría buscar y que aún no están en su lista.
Devuelve SOLO este JSON:
{{
  "roles": ["rol en español", "role in english", ...]
}}
Incluye cada rol en español e inglés como entradas separadas. Sin duplicar los que ya tiene."""

    try:
        result = chat_json(model=cfg["modelos"]["escritura"], prompt=prompt)
        roles = [r for r in result.get("roles", []) if r not in profile.cargo_objetivo]
        return {"roles": roles}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/cv/extract")
def extract_cv_profile():
    if not cv_exists():
        raise HTTPException(400, "No hay CV subido aún")
    try:
        profile = extract_profile()
        return {"ok": True, "profile": profile.model_dump()}
    except Exception as e:
        raise HTTPException(500, str(e))
