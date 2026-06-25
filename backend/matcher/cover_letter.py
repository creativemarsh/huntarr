from pathlib import Path

import yaml

from shared.models import Profile
from shared.ollama_client import chat

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "output" / "cartas"

_config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
MODELO_ESCRITURA: str = _config["modelos"]["escritura"]


def generar_carta(oferta: dict, profile: Profile) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"carta_{oferta['id']}.md"

    if output_path.exists():
        return output_path

    prompt = f"""Escribe una carta de presentación en español para esta oferta:

Cargo: {oferta['titulo']}
Empresa: {oferta['empresa']}
Descripción: {oferta['descripcion'][:1500]}

Candidato:
- Nombre: {profile.nombre}
- Skills: {", ".join(profile.skills)}
- Educación: {profile.educacion}
- Experiencia: {profile.experiencia_anos} años (estudiante)

REGLAS:
1. Máximo 3 párrafos cortos
2. Tono profesional pero cercano
3. Menciona 2-3 skills específicas que la oferta pide y el candidato tiene
4. No exageres la experiencia, es estudiante buscando su primer trabajo
5. Enfatiza motivación, ganas de aprender y aporte que puede hacer

Devuelve SOLO la carta, sin comentarios ni encabezados extra."""

    carta = chat(model=MODELO_ESCRITURA, prompt=prompt)
    output_path.write_text(carta, encoding="utf-8")
    return output_path
