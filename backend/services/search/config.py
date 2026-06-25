import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SEARCH_CONFIG_PATH = ROOT / "data" / "search_config.json"

DEFAULTS = {
    "terminos_auto": [],
    "terminos_usuario": [],
    "ubicacion": "Chile",
    "horas_atras": 168,
    "resultados_por_termino": 25,
    "modo_junior": False,
    "modo_senior": False,
    "modo_trainee": False,
    "modo_graduate": False,
    "modo_practicas": False,
}


def load() -> dict:
    if SEARCH_CONFIG_PATH.exists():
        return json.loads(SEARCH_CONFIG_PATH.read_text(encoding="utf-8"))
    return dict(DEFAULTS)


def save(data: dict) -> None:
    SEARCH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEARCH_CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_all_terms(cfg: dict) -> list[str]:
    auto = set(cfg.get("terminos_auto", []))
    usuario = set(cfg.get("terminos_usuario", []))
    return sorted(auto | usuario)


def get_search_terms(cfg: dict) -> list[str]:
    base = get_all_terms(cfg)
    expanded = list(base)
    if cfg.get("modo_junior"):
        expanded += [f"{t} junior" for t in base]
    if cfg.get("modo_senior"):
        expanded += [f"{t} senior" for t in base]
    if cfg.get("modo_trainee"):
        expanded += [f"{t} trainee" for t in base]
    if cfg.get("modo_graduate"):
        expanded += [f"graduate program {t}" for t in base] + [f"programa de graduados {t}" for t in base]
    if cfg.get("modo_practicas"):
        expanded += [f"{t} prácticas" for t in base] + [f"{t} intern" for t in base]
    seen = set()
    result = []
    for t in expanded:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def populate_from_profile(cargo_objetivo: list[str], ubicacion: str) -> None:
    cfg = load()
    cfg["terminos_auto"] = sorted(t.lower() for t in cargo_objetivo)
    if ubicacion and not cfg.get("ubicacion"):
        cfg["ubicacion"] = ubicacion
    save(cfg)
