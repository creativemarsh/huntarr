from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.search.config import load, save, get_all_terms

router = APIRouter()


class SearchConfigUpdate(BaseModel):
    terminos_usuario: Optional[list[str]] = None
    ubicacion: Optional[str] = None
    horas_atras: Optional[int] = None
    resultados_por_termino: Optional[int] = None
    modo_junior: Optional[bool] = None
    modo_senior: Optional[bool] = None
    modo_trainee: Optional[bool] = None
    modo_graduate: Optional[bool] = None
    modo_practicas: Optional[bool] = None


@router.get("/search/config")
def get_search_config():
    cfg = load()
    return {**cfg, "terminos_busqueda": get_all_terms(cfg)}


@router.post("/search/config")
def save_search_config(body: SearchConfigUpdate):
    cfg = load()
    if body.terminos_usuario is not None:
        cfg["terminos_usuario"] = body.terminos_usuario
    if body.ubicacion is not None:
        cfg["ubicacion"] = body.ubicacion
    if body.horas_atras is not None:
        if body.horas_atras < 1:
            raise HTTPException(400, "horas_atras debe ser mayor a 0")
        cfg["horas_atras"] = body.horas_atras
    if body.resultados_por_termino is not None:
        if body.resultados_por_termino < 1:
            raise HTTPException(400, "resultados_por_termino debe ser mayor a 0")
        cfg["resultados_por_termino"] = body.resultados_por_termino
    if body.modo_junior is not None:
        cfg["modo_junior"] = body.modo_junior
    if body.modo_senior is not None:
        cfg["modo_senior"] = body.modo_senior
    if body.modo_trainee is not None:
        cfg["modo_trainee"] = body.modo_trainee
    if body.modo_graduate is not None:
        cfg["modo_graduate"] = body.modo_graduate
    if body.modo_practicas is not None:
        cfg["modo_practicas"] = body.modo_practicas
    save(cfg)
    return {"ok": True}
