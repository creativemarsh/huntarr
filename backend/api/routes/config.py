import json
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.llm_client import chat, _load_config

ROOT = Path(__file__).parent.parent.parent
USER_CONFIG_PATH = ROOT / "data" / "user_config.json"

PROVIDERS = ["ollama", "openrouter"]

router = APIRouter()


class ConfigUpdate(BaseModel):
    proveedor: str
    api_key: Optional[str] = None
    modelo_filtro: Optional[str] = None
    modelo_escritura: Optional[str] = None
    ollama_base_url: Optional[str] = None


def _load_user_config() -> dict:
    if USER_CONFIG_PATH.exists():
        return json.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _save_user_config(data: dict) -> None:
    USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    USER_CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


@router.get("/config")
def get_config():
    user = _load_user_config()
    api_key_raw = user.get("openrouter_api_key", "")
    return {
        "proveedor": user.get("proveedor", "ollama"),
        "api_key_set": bool(api_key_raw),
        "api_key_preview": f"{api_key_raw[:8]}..." if api_key_raw else None,
        "modelo_filtro": user.get("modelo_filtro", "deepseek-r1:8b"),
        "modelo_escritura": user.get("modelo_escritura", "phi3.5"),
        "ollama_base_url": user.get("ollama_base_url", "http://localhost:11434"),
    }


@router.post("/config")
def save_config(body: ConfigUpdate):
    if body.proveedor not in PROVIDERS:
        raise HTTPException(400, f"Proveedor inválido. Opciones: {PROVIDERS}")

    user = _load_user_config()
    user["proveedor"] = body.proveedor

    if body.api_key is not None:
        user["openrouter_api_key"] = body.api_key

    if body.modelo_filtro is not None:
        user["modelo_filtro"] = body.modelo_filtro

    if body.modelo_escritura is not None:
        user["modelo_escritura"] = body.modelo_escritura

    if body.ollama_base_url is not None:
        user["ollama_base_url"] = body.ollama_base_url

    _save_user_config(user)
    return {"ok": True}


@router.post("/config/test")
def test_config():
    try:
        cfg = _load_config()
        model = cfg["modelos"]["escritura"]
        response = chat(model=model, prompt="Responde solo: ok")
        return {"ok": True, "response": response.strip()}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/providers/ollama/models")
def get_ollama_models():
    cfg = _load_config()
    base_url = cfg.get("ollama", {}).get("base_url", "http://localhost:11434")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"models": sorted(models)}
    except requests.exceptions.ConnectionError:
        raise HTTPException(503, "Ollama no está corriendo")
    except Exception as e:
        raise HTTPException(500, str(e))
