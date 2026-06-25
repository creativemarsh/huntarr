import json
import os
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent.parent

TIMEOUT = 600
MAX_RETRIES = 2
RETRY_DELAY = 5

_DEFAULTS = {
    "proveedor": "ollama",
    "ollama": {"base_url": "http://localhost:11434"},
    "openrouter": {},
    "modelos": {"filtro": "deepseek-r1:8b", "escritura": "phi3.5"},
}


def _load_config() -> dict:
    import copy
    cfg = copy.deepcopy(_DEFAULTS)
    user_path = ROOT / "data" / "user_config.json"
    if user_path.exists():
        user = json.loads(user_path.read_text(encoding="utf-8"))
        if "proveedor" in user:
            cfg["proveedor"] = user["proveedor"]
        if "openrouter_api_key" in user:
            cfg["openrouter"]["api_key"] = user["openrouter_api_key"]
        if "ollama_base_url" in user:
            cfg["ollama"]["base_url"] = user["ollama_base_url"]
        if "modelo_filtro" in user:
            cfg["modelos"]["filtro"] = user["modelo_filtro"]
        if "modelo_escritura" in user:
            cfg["modelos"]["escritura"] = user["modelo_escritura"]
    return cfg


def chat(model: str, prompt: str, json_mode: bool = False) -> str:
    cfg = _load_config()
    if cfg.get("proveedor") == "openrouter":
        return _chat_openrouter(model, prompt, json_mode, cfg)
    return _chat_ollama(model, prompt, json_mode, cfg)


def chat_json(model: str, prompt: str) -> dict:
    raw = chat(model, prompt, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


def _chat_ollama(model: str, prompt: str, json_mode: bool, cfg: dict) -> str:
    base_url = cfg.get("ollama", {}).get("base_url", "http://localhost:11434")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"

    last_error = None
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                print(f"  ⏱ Timeout (intento {attempt}/{MAX_RETRIES + 1}), reintentando en {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.HTTPError:
            raise
        except requests.exceptions.ConnectionError as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                print(f"  🔌 Sin conexión con Ollama (intento {attempt}/{MAX_RETRIES + 1}), reintentando en {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

    raise requests.exceptions.ReadTimeout(
        f"Ollama no respondió después de {MAX_RETRIES + 1} intentos"
    ) from last_error


def _chat_openrouter(model: str, prompt: str, json_mode: bool, cfg: dict) -> str:
    api_key = cfg.get("openrouter", {}).get("api_key", "")
    if not api_key:
        api_key_env = cfg.get("openrouter", {}).get("api_key_env", "OPENROUTER_API_KEY")
        api_key = os.environ.get(api_key_env, "")
    if not api_key:
        raise ValueError(
            "Falta la API key de OpenRouter. "
            "Guárdala desde el frontend o define la variable OPENROUTER_API_KEY."
        )

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                print(f"  ⏱ Timeout (intento {attempt}/{MAX_RETRIES + 1}), reintentando en {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.HTTPError:
            raise
        except requests.exceptions.ConnectionError as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                print(f"  🔌 Sin conexión con OpenRouter (intento {attempt}/{MAX_RETRIES + 1}), reintentando en {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

    raise requests.exceptions.ReadTimeout(
        f"OpenRouter no respondió después de {MAX_RETRIES + 1} intentos"
    ) from last_error
