import asyncio
import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.scorer import scorer as scorer_svc
from services.scraper.scraper import get_all_jobs
from services.cv.extractor import get_profile

ROOT = Path(__file__).parent.parent.parent
FEEDBACK_PATH = ROOT / "data" / "state" / "feedback.json"

router = APIRouter()


class FeedbackBody(BaseModel):
    rating: Literal["up", "down"]


def _load_feedback() -> dict:
    if not FEEDBACK_PATH.exists():
        return {}
    try:
        return json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_feedback(data: dict) -> None:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


@router.post("/ia/score")
def start_scoring():
    profile = get_profile()
    if not profile:
        raise HTTPException(400, "No hay perfil extraído. Sube y extrae tu CV primero.")
    jobs = get_all_jobs()
    if not jobs:
        raise HTTPException(400, "No hay ofertas scrapeadas.")
    started = scorer_svc.start(jobs, profile)
    if not started:
        raise HTTPException(409, "El scoring ya está en curso.")
    return {"ok": True, "total": len(jobs)}


@router.delete("/ia/scores")
def clear_scores():
    if scorer_svc.get_state()["running"]:
        raise HTTPException(409, "El scoring está en curso.")
    scorer_svc.clear()
    return {"ok": True}


@router.get("/ia/status")
def get_status():
    return scorer_svc.get_state()


@router.get("/ia/stale")
def get_stale():
    profile = get_profile()
    if not profile:
        return {"stale": False}
    return scorer_svc.get_stale_info(profile)


@router.get("/ia/results")
def get_results():
    jobs = get_all_jobs()
    results = scorer_svc.get_all_results(jobs)
    feedback = _load_feedback()
    for r in results:
        r["feedback"] = feedback.get(r["id"])
    return results


@router.post("/ia/feedback/{job_id}")
def set_feedback(job_id: str, body: FeedbackBody):
    feedback = _load_feedback()
    if feedback.get(job_id) == body.rating:
        del feedback[job_id]
    else:
        feedback[job_id] = body.rating
    _save_feedback(feedback)
    return {"ok": True, "rating": feedback.get(job_id)}


@router.get("/ia/events")
async def scorer_events():
    async def generate():
        idx = 0
        while True:
            new = scorer_svc.get_new_results(idx)
            for r in new:
                yield f"data: {json.dumps({'type': 'scored', 'result': r})}\n\n"
            idx += len(new)

            state = scorer_svc.get_state()

            if state["current"]:
                yield f"data: {json.dumps({'type': 'progress', 'current': state['scored'], 'total': state['total'], 'titulo': state['current']})}\n\n"

            if state["error"]:
                yield f"data: {json.dumps({'type': 'error', 'message': state['error']})}\n\n"
                break

            if state["done"] and not new:
                yield f"data: {json.dumps({'type': 'done', 'total': state['scored']})}\n\n"
                break

            await asyncio.sleep(1.0)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
