from pydantic import BaseModel, field_validator
from typing import Optional


class Profile(BaseModel):
    nombre: str = ""
    cargo_objetivo: list[str] = []
    skills: list[str] = []
    educacion: str = ""
    experiencia_anos: int = 0
    idiomas: list[str] = []
    resumen: str = ""

    @field_validator("educacion", "resumen", "nombre", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        if isinstance(v, list):
            return " ".join(str(i) for i in v)
        return v


class Oferta(BaseModel):
    id: str
    titulo: str
    empresa: str
    ubicacion: str
    url: str
    descripcion: str
    fecha_scrape: str
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None
    es_remoto: bool = False
    fuente: str = ""
    score: Optional[int] = None
    score_razon: Optional[str] = None


class PostulacionEstado(BaseModel):
    id: str
    empresa: str
    cargo: str
    fecha: str
    estado: str = "pendiente"


class State(BaseModel):
    procesadas: list[str] = []
    postuladas: list[PostulacionEstado] = []
