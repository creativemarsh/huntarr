import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from filter.filter import filtrar, SCORE_MINIMO
from matcher.cover_letter import generar_carta
from matcher.cv_adapter import adaptar_cv
from scraper.scraper import scrape
from shared.models import PostulacionEstado, State
from shared.profile import extract_profile

ROOT = Path(__file__).parent
JOBS_PATH = ROOT / "jobs.json"
STATE_PATH = ROOT / "state.json"
OUTPUT_DIR = ROOT / "output"
PROCESADAS_RETENTION_DAYS = 60


def load_state() -> State:
    if STATE_PATH.exists():
        return State(**json.loads(STATE_PATH.read_text(encoding="utf-8-sig")))
    return State()


def save_state(state: State) -> None:
    STATE_PATH.write_text(state.model_dump_json(indent=2), encoding="utf-8-sig")


def load_jobs() -> list[dict]:
    if JOBS_PATH.exists():
        content = JOBS_PATH.read_text(encoding="utf-8-sig").strip()
        if content:
            return json.loads(content)
    return []


def save_jobs(jobs: list[dict]) -> None:
    JOBS_PATH.write_text(
        json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )


def limpiar_procesadas(state: State, jobs: list[dict]) -> None:
    cutoff = datetime.now() - timedelta(days=PROCESADAS_RETENTION_DAYS)
    fecha_por_id = {}
    for j in jobs:
        try:
            fecha_por_id[j["id"]] = datetime.fromisoformat(j["fecha_scrape"])
        except (KeyError, ValueError):
            pass

    activas = {p.id for p in state.postuladas}
    antes = len(state.procesadas)
    state.procesadas = [
        id_
        for id_ in state.procesadas
        if id_ in activas or fecha_por_id.get(id_, cutoff) >= cutoff
    ]
    eliminadas = antes - len(state.procesadas)
    if eliminadas:
        print(f"  Limpieza: {eliminadas} IDs antiguos eliminados de procesadas")


def generar_diario(nuevas: list[dict], state: State, stats: dict) -> Path:
    env = Environment(loader=FileSystemLoader(str(OUTPUT_DIR / "templates")))
    estados = {p.id: p.estado for p in state.postuladas}

    def estado_emoji(estado: str) -> str:
        return {
            "postulado": "✅",
            "pendiente": "👀",
            "descartado": "❌",
            "en_proceso": "🔄",
            "rechazado": "💔",
        }.get(estado, "👀")

    env.globals["estado_emoji"] = estado_emoji

    aprobadas_render = []
    descartadas_render = []

    for o in nuevas:
        score = o.get("score", 0) or 0
        cv_path = OUTPUT_DIR / "cvs" / f"cv_{o['id']}.html"
        entry = {
            **o,
            "estado": estados.get(o["id"], "pendiente"),
            "cv_path": str(cv_path.relative_to(ROOT)).replace("\\", "/")
            if cv_path.exists()
            else None,
        }
        if score >= SCORE_MINIMO:
            aprobadas_render.append(entry)
        else:
            descartadas_render.append(entry)

    template = env.get_template("diario.j2")
    contenido = template.render(
        fecha=datetime.now().strftime("%Y-%m-%d"),
        aprobadas=aprobadas_render,
        descartadas=descartadas_render,
        **stats,
    )

    diario_path = OUTPUT_DIR / f"DIARIO_{datetime.now().strftime('%Y-%m-%d')}.md"
    diario_path.write_text(contenido, encoding="utf-8-sig")
    return diario_path


def main() -> None:
    print("=" * 52)
    print("  JobHunter Pipeline")
    print("=" * 52)

    state = load_state()
    jobs_existentes = load_jobs()

    print("\n[1/5] Cargando perfil del CV...")
    try:
        profile = extract_profile()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    print(f"  {profile.nombre} | {', '.join(profile.skills[:5])}")

    limpiar_procesadas(state, jobs_existentes)

    print("\n[2/5] Scrapeando ofertas...")
    todas = scrape()
    nuevas = [o for o in todas if o["id"] not in state.procesadas]
    print(f"  {len(nuevas)} ofertas nuevas (de {len(todas)} scrapeadas)")

    if not nuevas:
        print("\n  Sin ofertas nuevas. Pipeline terminado.")
        save_state(state)
        return

    print("\n[3/5] Filtrando con IA...")
    aprobadas = filtrar(nuevas, profile)
    print(f"\n  {len(aprobadas)}/{len(nuevas)} ofertas aprobadas")

    print("\n[4/5] Generando CVs y cartas...")
    ya_postuladas = {p.id for p in state.postuladas}
    for oferta in aprobadas:
        print(f"  → {oferta['empresa']}: {oferta['titulo']}")
        adaptar_cv(oferta)
        generar_carta(oferta, profile)
        state.procesadas.append(oferta["id"])
        if oferta["id"] not in ya_postuladas:
            state.postuladas.append(
                PostulacionEstado(
                    id=oferta["id"],
                    empresa=oferta["empresa"],
                    cargo=oferta["titulo"],
                    fecha=datetime.now().strftime("%Y-%m-%d"),
                    estado="pendiente",
                )
            )

    for oferta in nuevas:
        if oferta["id"] not in state.procesadas:
            state.procesadas.append(oferta["id"])

    print("\n[5/5] Guardando y generando reporte...")
    jobs_existentes.extend(nuevas)
    save_jobs(jobs_existentes)
    save_state(state)

    diario = generar_diario(
        nuevas=nuevas,
        state=state,
        stats={
            "total_scrapeadas": len(nuevas),
            "total_filtradas": len(aprobadas),
            "total_cvs": len(aprobadas),
        },
    )

    print(f"\n  Diario: {diario}")
    print("\n✅ Pipeline completado.\n")


if __name__ == "__main__":
    main()
