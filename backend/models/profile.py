from pydantic import BaseModel, field_validator


class Profile(BaseModel):
    nombre: str = ""
    cargo_objetivo: list[str] = []
    skills: list[str] = []
    educacion: str = ""
    experiencia_anos: int = 0
    idiomas: list[str] = []
    resumen: str = ""
    ubicacion: str = ""
    graduado: bool = False
    ano_graduacion: int | None = None
    sobre_mi: str = ""

    @field_validator("educacion", "resumen", "nombre", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        if isinstance(v, list):
            return " ".join(str(i) for i in v)
        return v

    @field_validator("idiomas", "skills", "cargo_objetivo", mode="before")
    @classmethod
    def coerce_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):
            return [f"{k} {val}".strip() for k, val in v.items()]
        if isinstance(v, str):
            return [v] if v.strip() else []
        return v

    @field_validator("sobre_mi", "ubicacion", mode="before")
    @classmethod
    def coerce_optional_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, list):
            return " ".join(str(i) for i in v)
        return v
