import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from services.cv.extractor import (
    cv_exists,
    profile_exists,
    get_profile,
    extract_profile,
    CV_PATH,
)

ROOT = Path(__file__).parent.parent.parent

router = APIRouter()


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


@router.post("/cv/extract")
def extract_cv_profile():
    if not cv_exists():
        raise HTTPException(400, "No hay CV subido aún")
    try:
        profile = extract_profile()
        return {"ok": True, "profile": profile.model_dump()}
    except Exception as e:
        raise HTTPException(500, str(e))
