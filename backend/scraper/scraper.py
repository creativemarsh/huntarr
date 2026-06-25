import hashlib
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from jobspy import scrape_jobs

CONFIG = yaml.safe_load(
    (Path(__file__).parent / "config.yaml").read_text(encoding="utf-8")
)
INPUT_MANUAL = Path(__file__).parent.parent / "data" / "input" / "manual"


def scrape() -> list[dict]:
    ofertas: list[dict] = []

    terminos = CONFIG["terminos_busqueda"]
    fuentes = CONFIG["fuentes"]
    for i, termino in enumerate(terminos):
        print(f"  Buscando: {termino!r}")
        for fuente in fuentes:
            try:
                kwargs = dict(
                    site_name=[fuente],
                    search_term=termino,
                    location=CONFIG["ubicacion"],
                    hours_old=CONFIG["horas_atras"],
                    results_wanted=CONFIG["resultados_por_termino"],
                )
                if fuente == "indeed":
                    kwargs["country_indeed"] = "Chile"
                df = scrape_jobs(**kwargs)
                lote = _df_to_list(df)
                ofertas.extend(lote)
                print(f"    {fuente}: {len(lote)} encontradas")
            except Exception as e:
                print(f"  ⚠ Error en {fuente} buscando '{termino}': {e}")
        if i < len(terminos) - 1:
            time.sleep(3)

    return _dedup(ofertas)


def _df_to_list(df: pd.DataFrame) -> list[dict]:
    result = []
    for _, row in df.iterrows():
        url = str(row.get("job_url", "")).strip()
        if not url:
            continue
        result.append(
            {
                "id": hashlib.md5(url.encode()).hexdigest()[:12],
                "titulo": str(row.get("title", "")),
                "empresa": str(row.get("company", "")),
                "ubicacion": str(row.get("location", "")),
                "url": url,
                "descripcion": str(row.get("description", ""))[:3000],
                "fecha_scrape": datetime.now().isoformat(),
                "salario_min": _safe_float(row.get("min_amount")),
                "salario_max": _safe_float(row.get("max_amount")),
                "es_remoto": bool(row.get("is_remote", False)),
                "fuente": str(row.get("site", "")),
            }
        )
    return result


def _dedup(ofertas: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique = []
    for o in ofertas:
        if o["url"] not in seen:
            seen.add(o["url"])
            unique.append(o)
    return unique


def _safe_float(val) -> float | None:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None
