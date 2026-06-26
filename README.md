# Huntarr

Herramienta local de búsqueda de empleo con IA. Scrapea ofertas de trabajo, las puntúa según tu perfil, adapta tu CV para cada oferta y genera cartas de presentación — todo desde una interfaz web, sin enviar tus datos a terceros.

---

## Qué hace

1. **Scraping** — busca ofertas en Indeed, LinkedIn, GetOnBoard y otros portales usando los términos configurados.
2. **Scoring con IA** — evalúa cada oferta del 0 al 100 según tu perfil (experiencia, skills, ubicación, idiomas). Opcionalmente añade criterio propio: detecta red flags y valor de transición.
3. **Adaptación de CV** — genera un CV en Markdown/HTML adaptado al lenguaje de cada oferta aprobada.
4. **Carta de presentación** — genera una carta personalizada por oferta.
5. **Perfil** — extrae tu perfil desde tu CV en PDF y te permite editarlo desde la interfaz.

---

## Arquitectura

```
huntarr/
├── backend/   FastAPI (Python) — scraping, scoring, CV, perfil
└── frontend/  Next.js — interfaz web
```

El frontend corre en `localhost:3000` y consume la API del backend en `localhost:8000`.

---

## Requisitos

- **Python 3.10+**
- **Node.js 18+**
- **Ollama** (para modelos locales) — [ollama.com](https://ollama.com)
- O una **API key de OpenRouter** (para modelos en la nube)

---

## Instalación

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install python-jobspy --no-deps
```

> `python-jobspy` se instala sin deps porque su `numpy==1.26.3` no compila en Python 3.12+.

### Frontend

```powershell
cd frontend
npm install
```

### Modelos (si usas Ollama)

```powershell
ollama pull qwen2.5:7b-q4_K_M   # scoring — reemplaza por cualquier modelo instalado
ollama pull phi3.5               # escritura de CV y cartas
```

---

## Cómo arrancar

Abrir dos terminales:

```powershell
# Terminal 1 — backend
cd backend
.venv\Scripts\activate
uvicorn main:app --reload
```

```powershell
# Terminal 2 — frontend
cd frontend
npm run dev
```

Luego abrir [http://localhost:3000](http://localhost:3000).

---

## Primeros pasos

1. Ir a **Configuración** y elegir proveedor (Ollama o OpenRouter), modelos y términos de búsqueda.
2. Subir tu CV en la sección **CV** — el perfil se extrae automáticamente.
3. Ir a **Ofertas** y hacer scraping.
4. Ir a **IA** y calificar las ofertas scrapeadas.
5. Las ofertas con score alto quedan disponibles para generar CV adaptado y carta.

---

## Configuración desde la UI

| Sección | Qué configura |
|---|---|
| Proveedor | Ollama (local) u OpenRouter (nube) |
| Modelos | Modelo de scoring y modelo de escritura |
| Búsqueda | Términos, ubicación, recencia, modos (junior/senior/trainee) |
| Comportamiento IA | Criterio propio: red flags, alineación de carrera, valor de transición |

---

## Solución de problemas

| Problema | Solución |
|---|---|
| Backend no arranca | Verificar que el venv está activo y las deps instaladas |
| `ollama: command not found` | Instalar Ollama o agregarlo al PATH |
| Modelo no encontrado (404) | Verificar con `ollama list` que el modelo está descargado |
| Scoring muy lento | Normal con modelos grandes en CPU — usar un modelo 3B–7B Q4 para tu GPU |
| Sin ofertas scrapeadas | Verificar términos de búsqueda en Configuración |
