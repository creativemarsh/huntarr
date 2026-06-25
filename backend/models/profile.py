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

    @field_validator("educacion", "resumen", "nombre", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        if isinstance(v, list):
            return " ".join(str(i) for i in v)
        return v
