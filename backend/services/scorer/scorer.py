import json
import threading
from datetime import datetime
from pathlib import Path

from models.profile import Profile
from services.llm.client import chat_json, _load_config

ROOT = Path(__file__).parent.parent.parent
SCORES_PATH = ROOT / "data" / "state" / "scores.json"

_lock = threading.Lock()
_state: dict = {
    "running": False,
    "done": False,
    "total": 0,
    "scored": 0,
    "current": "",
    "error": None,
    "results": [],
}

def clear() -> None:
    with _lock:
        _state["running"] = False
        _state["done"] = False
        _state["total"] = 0
        _state["scored"] = 0
        _state["current"] = ""
        _state["error"] = None
        _state["results"] = []
    if SCORES_PATH.exists():
        SCORES_PATH.unlink()


TITLE_KEYWORDS = {
    "data", "datos", "cloud", "aws", "gcp", "azure",
    "etl", "bi", "analytics", "spark", "kafka", "terraform",
    "databricks", "airflow", "dbt", "machine learning", "mlops", "devops",
    "data engineer", "data analyst", "ingeniero de datos", "analista de datos",
    "data scientist", "python", "sql", "pipeline", "sysops",
    "developer", "desarrollador", "fullstack", "full stack", "backend",
    "ia", "inteligencia artificial", "software", "sistemas", "informática",
}

_PROMPT = """Eres un evaluador de ofertas de trabajo para un candidato con el siguiente perfil:

CANDIDATO:
- Cargos que busca: {cargo_objetivo}
- Skills técnicas: {skills}
- Años de experiencia: {experiencia_anos}
- Educación: {educacion}
- Idiomas: {idiomas}
- Ubicación: {candidato_ubicacion}
- Resumen: {resumen}

OFERTA:
Título: {titulo}
Empresa: {empresa}
Ubicación: {oferta_ubicacion}{remoto_str}
Descripción:
{descripcion}

Evalúa qué tan bien encaja esta oferta con el candidato y devuelve SOLO este JSON:
{{
  "score": <número entero del 0 al 100>,
  "razon": "<una sola oración explicando el score>"
}}

Criterios de puntuación base:
- 0: Sin relación con el perfil (médico, vendedor, operario, etc.)
- 10-40: Relacionada con TI pero no con el área del candidato
- 41-60: Parcialmente relacionada (ej: QA con SQL, web con Python)
- 61-80: Directamente relacionada, acepta el nivel de experiencia del candidato
- 81-100: Exactamente lo que busca, menciona skills específicas del candidato

Penalizaciones obligatorias (aplica SIEMPRE, no son opcionales):

AÑOS DE EXPERIENCIA:
- Busca en "Basic Qualifications", "Required", "Requisitos" o secciones similares si hay un requisito de años (ej: "3+ years", "4+ años", "mínimo 5 años").
- Ignora el lenguaje motivacional ("si recién estás comenzando", "don't let it stop you", etc.) — ese texto NO cancela los requisitos duros.
- Si la oferta requiere MÁS años de los que tiene el candidato ({experiencia_anos} años), aplica esta escala de penalización sobre el score base:
  - Diferencia de 1-2 años: resta 10 puntos
  - Diferencia de 3-4 años: resta 25 puntos
  - Diferencia de 5+ años: resta 40 puntos
- Cuando apliques esta penalización, la `razon` DEBE mencionar explícitamente cuántos años pide la oferta y cuántos tiene el candidato (ej: "pide 4+ años de experiencia pero el candidato tiene 0").

IDIOMAS:
- Si la oferta requiere un idioma específico Y el candidato NO tiene ese idioma en su lista de idiomas: score MÁXIMO 45, sin excepción. Aplica a cualquier idioma.

UBICACIÓN:
- Si la oferta NO es remota Y la ciudad de la oferta es distinta a la del candidato: descuenta 20 puntos del score base.

Devuelve SOLO el JSON, sin texto adicional."""


def get_state() -> dict:
    with _lock:
        return {
            "running": _state["running"],
            "done": _state["done"],
            "total": _state["total"],
            "scored": _state["scored"],
            "current": _state["current"],
            "error": _state["error"],
        }


def get_new_results(from_index: int) -> list[dict]:
    with _lock:
        return _state["results"][from_index:]


def load_scores() -> dict:
    if not SCORES_PATH.exists():
        return {}
    try:
        return json.loads(SCORES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_all_results(jobs: list[dict]) -> list[dict]:
    scores = load_scores()
    results = []
    for job in jobs:
        if job["id"] in scores:
            results.append({**job, **scores[job["id"]]})
    return sorted(results, key=lambda j: j.get("score", 0), reverse=True)


def start(jobs: list[dict], profile: Profile) -> bool:
    with _lock:
        if _state["running"]:
            return False
        _state["running"] = True
        _state["done"] = False
        _state["error"] = None
        _state["results"] = []
        _state["total"] = len(jobs)
        _state["scored"] = 0
        _state["current"] = ""

    thread = threading.Thread(target=_run, args=(jobs, profile), daemon=True)
    thread.start()
    return True


def _run(jobs: list[dict], profile: Profile) -> None:
    try:
        cfg = _load_config()
        modelo = cfg["modelos"]["filtro"]
        proveedor = cfg.get("proveedor", "ollama")
        print(f"[scorer] proveedor={proveedor} modelo={modelo} jobs={len(jobs)}")

        existing_scores = load_scores()

        for job in jobs:
            with _lock:
                _state["current"] = job.get("titulo", "")

            if job["id"] in existing_scores:
                score_data = existing_scores[job["id"]]
            else:
                titulo = job.get("titulo", "").lower()
                if not any(kw in titulo for kw in TITLE_KEYWORDS):
                    score_data = {
                        "score": 0,
                        "razon": "Sin relación con el perfil técnico buscado",
                        "scored_at": datetime.now().isoformat(),
                    }
                else:
                    score_data = _score_job(job, profile)
                existing_scores[job["id"]] = score_data

            with _lock:
                _state["results"].append({**job, **score_data})
                _state["scored"] += 1

        _save_scores(existing_scores)

    except Exception as e:
        with _lock:
            _state["error"] = str(e)
    finally:
        with _lock:
            _state["running"] = False
            _state["done"] = True
            _state["current"] = ""


def _score_job(job: dict, profile: Profile) -> dict:
    es_remoto = job.get("es_remoto", False)
    remoto_str = " (Remoto)" if es_remoto else ""
    prompt = _PROMPT.format(
        cargo_objetivo=", ".join(profile.cargo_objetivo),
        skills=", ".join(profile.skills),
        experiencia_anos=profile.experiencia_anos,
        educacion=profile.educacion,
        idiomas=", ".join(profile.idiomas) if profile.idiomas else "No especificado",
        candidato_ubicacion=profile.ubicacion or "No especificada",
        resumen=profile.resumen,
        titulo=job.get("titulo", ""),
        empresa=job.get("empresa", ""),
        oferta_ubicacion=job.get("ubicacion", "") or "No especificada",
        remoto_str=remoto_str,
        descripcion=job.get("descripcion", "")[:1500],
    )
    try:
        cfg = _load_config()
        result = chat_json(model=cfg["modelos"]["filtro"], prompt=prompt)
        return {
            "score": max(0, min(100, int(result.get("score", 0)))),
            "razon": str(result.get("razon", "")),
            "scored_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "score": 0,
            "razon": f"Error al evaluar: {e}",
            "scored_at": datetime.now().isoformat(),
        }


def _save_scores(scores: dict) -> None:
    SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCORES_PATH.write_text(json.dumps(scores, indent=2, ensure_ascii=False), encoding="utf-8")
