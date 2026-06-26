import hashlib
import json
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

ROOT = Path(__file__).parent.parent.parent
JOBS_PATH = ROOT / "data" / "state" / "jobs.json"

_lock = threading.Lock()

_state: dict = {
    "running": False,
    "done": False,
    "cancelled": False,
    "current_term": "",
    "jobs": [],
    "error": None,
}


def get_state() -> dict:
    with _lock:
        return {
            "running": _state["running"],
            "done": _state["done"],
            "current_term": _state["current_term"],
            "total": len(_state["jobs"]),
            "error": _state["error"],
        }


def get_new_jobs(from_index: int) -> list[dict]:
    with _lock:
        return _state["jobs"][from_index:]


def get_all_jobs() -> list[dict]:
    if not JOBS_PATH.exists():
        return []
    try:
        return json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def start(cfg: dict, terms: list[str]) -> bool:
    with _lock:
        if _state["running"]:
            return False
        _state["running"] = True
        _state["done"] = False
        _state["cancelled"] = False
        _state["error"] = None
        _state["jobs"] = []
        _state["current_term"] = ""

    thread = threading.Thread(target=_run, args=(cfg, terms), daemon=True)
    thread.start()
    return True


def _run(cfg: dict, terms: list[str]) -> None:
    try:
        existing_ids = _load_existing_ids()

        for i, term in enumerate(terms):
            with _lock:
                _state["current_term"] = term

            for df in _scrape_all(term, cfg):
                if not df.empty:
                    df = df[df["job_url"].apply(
                        lambda u: bool(u) and str(u).strip() != "" and
                        hashlib.md5(str(u).strip().encode()).hexdigest()[:12] not in existing_ids
                    )]
                jobs = _df_to_list(df)
                for job in jobs:
                    existing_ids.add(job["id"])
                    with _lock:
                        _state["jobs"].append(job)

            with _lock:
                if _state["cancelled"]:
                    break

            if i < len(terms) - 1:
                time.sleep(2)

        _save_jobs()

    except Exception as e:
        with _lock:
            _state["error"] = str(e)
    finally:
        with _lock:
            _state["running"] = False
            _state["done"] = True
            _state["current_term"] = ""


def cancel() -> bool:
    with _lock:
        if not _state["running"]:
            return False
        _state["cancelled"] = True
    return True


def clear() -> None:
    with _lock:
        _state["running"] = False
        _state["done"] = False
        _state["error"] = None
        _state["jobs"] = []
        _state["current_term"] = ""
    if JOBS_PATH.exists():
        JOBS_PATH.unlink()


def _load_existing_ids() -> set:
    if not JOBS_PATH.exists():
        return set()
    try:
        jobs = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
        return {j["id"] for j in jobs}
    except Exception:
        return set()


def _save_jobs() -> None:
    existing: list[dict] = []
    if JOBS_PATH.exists():
        try:
            existing = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    with _lock:
        new_jobs = list(_state["jobs"])

    existing_ids = {j["id"] for j in existing}
    for job in new_jobs:
        if job["id"] not in existing_ids:
            existing.append(job)

    JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOBS_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def _google_time_phrase(hours: int) -> str:
    if hours <= 24:
        return "since yesterday"
    if hours <= 72:
        return "in the last 3 days"
    if hours <= 168:
        return "in the last week"
    return "in the last month"


def _scrape_all(term: str, cfg: dict):
    location = cfg.get("ubicacion", "Chile")
    hours = cfg.get("horas_atras", 168)
    results = cfg.get("resultados_por_termino", 25)

    # Indeed + LinkedIn
    try:
        yield scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=f'"{term}"',
            location=location,
            hours_old=hours,
            results_wanted=results,
            country_indeed="Chile",
            linkedin_fetch_description=True,
        )
    except Exception:
        yield pd.DataFrame()

    time.sleep(2)

    # Google Jobs
    try:
        google_query = f'{term} jobs near {location} {_google_time_phrase(hours)}'
        yield scrape_jobs(
            site_name="google",
            google_search_term=google_query,
            results_wanted=results,
        )
    except Exception:
        yield pd.DataFrame()


def _df_to_list(df: pd.DataFrame) -> list[dict]:
    result = []
    for _, row in df.iterrows():
        url = str(row.get("job_url", "")).strip()
        if not url:
            continue
        result.append({
            "id": hashlib.md5(url.encode()).hexdigest()[:12],
            "titulo": str(row.get("title", "")),
            "empresa": str(row.get("company", "")),
            "ubicacion": str(row.get("location", "")),
            "url": url,
            "descripcion": str(row.get("description", ""))[:8000],
            "fecha_scrape": datetime.now().isoformat(),
            "fecha_publicacion": _safe_date(row.get("date_posted")),
            "salario_min": _safe_float(row.get("min_amount")),
            "salario_max": _safe_float(row.get("max_amount")),
            "es_remoto": bool(row.get("is_remote", False)),
            "fuente": str(row.get("site", "")),
        })
    return result


def _safe_date(val) -> str | None:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    try:
        if hasattr(val, "isoformat"):
            return val.isoformat()
        return str(val)
    except Exception:
        return None


def _safe_float(val) -> float | None:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None
