import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from services.scraper import scraper as scraper_svc
from services.search.config import load as load_search_cfg, get_search_terms

router = APIRouter()


@router.post("/scraper/start")
def start_scraper():
    cfg = load_search_cfg()
    terms = get_search_terms(cfg)
    if not terms:
        raise HTTPException(400, "No hay términos de búsqueda configurados")
    started = scraper_svc.start(cfg, terms)
    if not started:
        raise HTTPException(409, "El scraping ya está en curso")
    return {"ok": True, "terms_count": len(terms)}


@router.delete("/scraper/jobs")
def clear_jobs():
    if scraper_svc.get_state()["running"]:
        raise HTTPException(409, "No se puede limpiar mientras el scraping está en curso")
    scraper_svc.clear()
    return {"ok": True}


@router.get("/scraper/status")
def get_status():
    return scraper_svc.get_state()


@router.get("/scraper/events")
async def scraper_events():
    async def generate():
        idx = 0
        while True:
            new_jobs = scraper_svc.get_new_jobs(idx)
            for job in new_jobs:
                yield f"data: {json.dumps({'type': 'job', 'job': job})}\n\n"
            idx += len(new_jobs)

            state = scraper_svc.get_state()

            if state["current_term"]:
                yield f"data: {json.dumps({'type': 'progress', 'term': state['current_term'], 'total': state['total']})}\n\n"

            if state["error"]:
                yield f"data: {json.dumps({'type': 'error', 'message': state['error']})}\n\n"
                break

            if state["done"] and not new_jobs:
                yield f"data: {json.dumps({'type': 'done', 'total': state['total']})}\n\n"
                break

            await asyncio.sleep(0.8)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
