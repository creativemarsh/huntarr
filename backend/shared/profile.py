import json
from pathlib import Path

import pdfplumber
import yaml

from .models import Profile
from .ollama_client import chat_json

ROOT = Path(__file__).parent.parent
PROFILE_PATH = ROOT / "data" / "state" / "profile.json"
CV_PATH = ROOT / "data" / "input" / "cv_base.pdf"

_config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
MODELO_ESCRITURA: str = _config["modelos"]["escritura"]


def read_pdf(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def extract_profile() -> Profile:
    if PROFILE_PATH.exists():
        return Profile(**json.loads(PROFILE_PATH.read_text(encoding="utf-8")))

    if not CV_PATH.exists():
        raise FileNotFoundError(
            f"\n❌ No se encontró el CV en: {CV_PATH}\n"
            "   Copia tu CV como  data/input/cv_base.pdf  y vuelve a correr el pipeline.\n"
        )

    print("  Extrayendo perfil del CV (solo ocurre la primera vez)...")
    cv_text = read_pdf(CV_PATH)

    profile_data = chat_json(
        model=MODELO_ESCRITURA,
        prompt=f"""Analiza el siguiente CV y extrae la información en formato JSON con esta estructura exacta:
{{
  "nombre": "nombre completo del candidato",
  "cargo_objetivo": ["lista de cargos que busca, inferidos del CV"],
  "skills": ["lista de habilidades técnicas encontradas"],
  "educacion": "carrera e institución de estudios",
  "experiencia_anos": 0,
  "idiomas": ["lista de idiomas mencionados"],
  "resumen": "resumen profesional de 2 oraciones basado en el CV"
}}

Si el candidato es estudiante o no tiene experiencia laboral, experiencia_anos debe ser 0.
Para cargo_objetivo, infiere roles apropiados según las skills y carrera estudiada.

CV:
{cv_text}

Devuelve SOLO el JSON, sin texto adicional.""",
    )

    profile = Profile(**profile_data)
    PROFILE_PATH.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    print("  Perfil guardado en profile.json")
    return profile
