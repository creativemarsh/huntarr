import json
from pathlib import Path

import pdfplumber

from models.profile import Profile
from services.llm.client import chat_json, _load_config
from services.search.config import populate_from_profile

ROOT = Path(__file__).parent.parent.parent
CV_PATH = ROOT / "data" / "input" / "cv_base.pdf"
PROFILE_PATH = ROOT / "data" / "state" / "profile.json"


def read_pdf(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def cv_exists() -> bool:
    return CV_PATH.exists()


def profile_exists() -> bool:
    return PROFILE_PATH.exists()


def get_profile() -> Profile | None:
    if not PROFILE_PATH.exists():
        return None
    return Profile(**json.loads(PROFILE_PATH.read_text(encoding="utf-8")))


def extract_profile() -> Profile:
    cv_text = read_pdf(CV_PATH)

    profile_data = chat_json(
        model=_load_config()["modelos"]["escritura"],
        prompt=f"""Analiza el siguiente CV y extrae la información en formato JSON con esta estructura exacta:
{{
  "nombre": "nombre completo del candidato",
  "cargo_objetivo": ["lista de cargos que busca, inferidos del CV"],
  "skills": ["lista de habilidades técnicas encontradas"],
  "educacion": "carrera e institución de estudios",
  "experiencia_anos": 0,
  "idiomas": ["lista de idiomas mencionados"],
  "resumen": "resumen profesional de 2 oraciones basado en el CV",
  "ubicacion": "ciudad o país donde reside o busca trabajo el candidato, inferido del CV",
  "graduado": false,
  "ano_graduacion": null
}}

REGLAS IMPORTANTES:

1. experiencia_anos: años de experiencia laboral real (prácticas/internships cuentan parcialmente). Si es estudiante sin experiencia, pon 0.

2. graduado: true si ya terminó y obtuvo el título. false si aún está estudiando.
   ano_graduacion: año en que obtuvo o espera obtener el título (ej: 2024). null si no se puede inferir.

3. cargo_objetivo: lista de roles inferidos del CV, cada uno en ESPAÑOL e INGLÉS.

   REGLAS ESTRICTAS:
   - Genera SOLO el rol base, SIN ningún sufijo de nivel (sin Junior, Senior, Trainee, ni ningún otro).
   - Cada entrada de la lista debe ser UN SOLO cargo. NUNCA juntes dos con "/".
   - Crea ENTRADAS SEPARADAS para español e inglés.

   Ejemplo correcto: ["Ingeniero de Datos", "Data Engineer", "Desarrollador Backend", "Backend Developer"]
   Ejemplo INCORRECTO: ["Ingeniero de Datos / Data Engineer", "Data Engineer Junior"]

   Pares de referencia (cada uno va como entrada separada):
   "Desarrollador Backend" y "Backend Developer"
   "Ingeniero de Software" y "Software Engineer"
   "Analista de Datos" y "Data Analyst"
   "Científico de Datos" y "Data Scientist"
   "Ingeniero de Datos" y "Data Engineer"

4. idiomas: incluye siempre el idioma en que está escrito el CV como primer idioma del candidato.
   Agrega únicamente idiomas declarados explícitamente (ej: sección "Idiomas", "Languages", o frases como "nivel B2", "fluido", "nativo").
   NO incluyas un idioma por el hecho de que el CV tenga términos técnicos en ese idioma (Python, SQL, etc. no son idiomas del candidato).
   NO inventes ni inferras idiomas que no estén explícitamente declarados.

5. ubicacion: usa el país o ciudad que aparece en el CV; si no hay dato claro, deja vacío.

CV:
{cv_text}

Devuelve SOLO el JSON, sin texto adicional.""",
    )

    for field in ("cargo_objetivo", "skills", "idiomas"):
        if isinstance(profile_data.get(field), list):
            seen = set()
            profile_data[field] = [
                x for x in profile_data[field]
                if x and x.lower() not in seen and not seen.add(x.lower())
            ]

    profile = Profile(**profile_data)
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    populate_from_profile(profile.cargo_objetivo, profile.ubicacion)
    return profile
