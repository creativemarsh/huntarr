import json
import re
import time

import requests

OLLAMA_BASE = "http://localhost:11434"
TIMEOUT = 600
MAX_RETRIES = 2
RETRY_DELAY = 5  # segundos entre reintentos


def chat(model: str, prompt: str, json_mode: bool = False) -> str:
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
            resp = requests.post(
                f"{OLLAMA_BASE}/api/chat", json=payload, timeout=TIMEOUT
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                print(f"  ⏱ Timeout (intento {attempt}/{MAX_RETRIES + 1}), reintentando en {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.HTTPError:
            raise  # 404 modelo no encontrado, etc. — no tiene sentido reintentar
        except requests.exceptions.ConnectionError as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                print(f"  🔌 Sin conexión con Ollama (intento {attempt}/{MAX_RETRIES + 1}), reintentando en {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

    raise requests.exceptions.ReadTimeout(
        f"Ollama no respondió después de {MAX_RETRIES + 1} intentos"
    ) from last_error


def chat_json(model: str, prompt: str) -> dict:
    raw = chat(model, prompt, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise
