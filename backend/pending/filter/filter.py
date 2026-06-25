from pathlib import Path

import yaml

from shared.models import Profile
from shared.llm_client import chat_json, _load_config

ROOT = Path(__file__).parent.parent
CONFIG = yaml.safe_load(
    (Path(__file__).parent / "config.yaml").read_text(encoding="utf-8")
)

PROMPT = (
    Path(__file__).parent / "prompts" / "ranking.txt"
).read_text(encoding="utf-8")

SCORE_MINIMO: int = CONFIG["score_minimo"]

# Verificado solo en el TÍTULO — en descripciones "datos" aparece en cualquier oferta
TITLE_KEYWORDS = {
    "data", "datos", "cloud", "aws", "gcp", "azure",
    "etl", "bi", "analytics", "spark", "kafka", "terraform",
    "databricks", "airflow", "dbt", "machine learning", "mlops", "devops",
    "data engineer", "data analyst", "ingeniero de datos", "analista de datos",
    "data scientist", "python", "sql", "pipeline", "sysops",
    "developer", "desarrollador", "fullstack", "full stack", "backend",
}


def filtrar(ofertas: list[dict], profile: Profile) -> list[dict]:
    aprobadas = []

    # Pre-filtro por keywords en el título — sin LLM
    relevantes = []
    for oferta in ofertas:
        if _tiene_keywords(oferta):
            relevantes.append(oferta)
        else:
            oferta["score"] = 0
            oferta["score_razon"] = "Sin keywords relevantes"
            print(f"  ⚡   0 — {oferta['empresa']}: {oferta['titulo']}")

    print(f"  Pre-filtro: {len(relevantes)}/{len(ofertas)} pasan al LLM")

    # Scoring individual por oferta
    for oferta in relevantes:
        score, razon = _score_oferta(oferta, profile)
        oferta["score"] = score
        oferta["score_razon"] = razon
        estado = "✅" if score >= SCORE_MINIMO else "❌"
        print(f"  {estado} {score:3d} — {oferta['empresa']}: {oferta['titulo']}")
        if score >= SCORE_MINIMO:
            aprobadas.append(oferta)

    return aprobadas


def _tiene_keywords(oferta: dict) -> bool:
    titulo = oferta.get("titulo", "").lower()
    return any(kw in titulo for kw in TITLE_KEYWORDS)


def _score_oferta(oferta: dict, profile: Profile) -> tuple[int, str]:
    prompt = PROMPT.format(
        cargo_objetivo=", ".join(profile.cargo_objetivo),
        skills=", ".join(profile.skills),
        experiencia_anos=profile.experiencia_anos,
        educacion=profile.educacion,
        resumen=profile.resumen,
        titulo=oferta["titulo"],
        empresa=oferta["empresa"],
        descripcion=oferta["descripcion"][:1000],
    )
    try:
        result = chat_json(model=_load_config()["modelos"]["filtro"], prompt=prompt)
        return int(result.get("score", 0)), str(result.get("razon", ""))
    except Exception as e:
        print(f"    ⚠ Error evaluando: {e}")
        return 0, "Error al evaluar"
