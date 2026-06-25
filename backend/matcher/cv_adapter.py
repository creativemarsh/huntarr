from pathlib import Path

import markdown as md_lib
import yaml

from shared.llm_client import chat
from shared.profile import read_pdf

CSS = """
body { font-family: Arial, sans-serif; max-width: 820px; margin: 40px auto; padding: 0 24px; color: #1a1a1a; font-size: 14px; line-height: 1.5; }
h1 { font-size: 22px; margin-bottom: 2px; }
h2 { font-size: 15px; border-bottom: 1px solid #ccc; padding-bottom: 3px; margin-top: 18px; text-transform: uppercase; letter-spacing: .05em; }
h3 { font-size: 14px; margin-bottom: 2px; }
ul { margin: 4px 0 8px 18px; padding: 0; }
li { margin-bottom: 2px; }
p { margin: 4px 0; }
a { color: #1a1a1a; }
@media print { body { margin: 20px; } }
"""

ROOT = Path(__file__).parent.parent
CV_PATH = ROOT / "data" / "input" / "cv_base.pdf"
OUTPUT_DIR = ROOT / "data" / "output" / "cvs"

_config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
MODELO_ESCRITURA: str = _config["modelos"]["escritura"]


def adaptar_cv(oferta: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"cv_{oferta['id']}.md"

    if output_path.exists():
        return output_path

    cv_text = read_pdf(CV_PATH)[:3000]

    prompt = f"""Eres un editor de CVs. Tu única tarea es reorganizar el CV existente para destacar lo más relevante para una oferta.

=== CV ORIGINAL (única fuente de contenido permitida) ===
{cv_text}
=== FIN DEL CV ORIGINAL ===

=== OFERTA (solo para entender qué destacar, NO copies nada de aquí al CV) ===
Cargo: {oferta['titulo']}
Empresa: {oferta['empresa']}
{oferta['descripcion'][:800]}
=== FIN DE LA OFERTA ===

Genera el CV adaptado en Markdown siguiendo estas reglas estrictamente:
1. USA ÚNICAMENTE información que ya existe en el CV original — palabra por palabra si es posible
2. NO copies ni parafrasees texto de la oferta de trabajo en el CV
3. NO inventes experiencias, proyectos ni skills que no estén en el CV original
4. Reordena las secciones poniendo primero lo más relevante para la oferta
5. Puedes ajustar el orden de los bullet points dentro de cada sección
6. Máximo 1 página equivalente, bullet points concisos
7. Mantén el nombre, contacto y educación del candidato tal como están

Devuelve SOLO el Markdown del CV. Sin explicaciones, sin comentarios."""

    cv_adaptado = chat(model=MODELO_ESCRITURA, prompt=prompt)
    output_path.write_text(cv_adaptado, encoding="utf-8")

    html_path = OUTPUT_DIR / f"cv_{oferta['id']}.html"
    body = md_lib.markdown(cv_adaptado, extensions=["extra"])
    html_path.write_text(
        f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        f"<title>CV — {oferta['empresa']}</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>",
        encoding="utf-8",
    )
    return output_path
