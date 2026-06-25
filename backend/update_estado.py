"""Actualiza el estado de una postulación.

Uso:
    python update_estado.py <id_oferta> <nuevo_estado>

Estados válidos:
    pendiente | postulado | descartado | en_proceso | rechazado

Ejemplo:
    python update_estado.py abc123def456 postulado
"""
import json
import sys
from pathlib import Path

from shared.models import State

STATE_PATH = Path(__file__).parent / "state.json"
ESTADOS_VALIDOS = ["pendiente", "postulado", "descartado", "en_proceso", "rechazado"]


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    id_oferta, nuevo_estado = sys.argv[1], sys.argv[2]

    if nuevo_estado not in ESTADOS_VALIDOS:
        print(f"Estado inválido. Opciones: {', '.join(ESTADOS_VALIDOS)}")
        sys.exit(1)

    if not STATE_PATH.exists():
        print("No existe state.json. Corre el pipeline primero.")
        sys.exit(1)

    state = State(**json.loads(STATE_PATH.read_text(encoding="utf-8")))

    for p in state.postuladas:
        if p.id == id_oferta:
            p.estado = nuevo_estado
            STATE_PATH.write_text(state.model_dump_json(indent=2), encoding="utf-8")
            print(f"✅ {p.empresa} — {p.cargo}: {nuevo_estado}")
            return

    print(f"No se encontró oferta con id '{id_oferta}'")
    print("\nIDs disponibles:")
    for p in state.postuladas:
        print(f"  {p.id}  {p.empresa} — {p.cargo} [{p.estado}]")


if __name__ == "__main__":
    main()
