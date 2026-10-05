"""Configuración común del contrato; no contiene acceso HTTP ni a la BD."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Rol = Literal['admin', 'tecnico', 'recepcion']


class Contrato(BaseModel):
    """Valida tipos sin conversiones silenciosas e ignora campos extra del servidor."""
    model_config = ConfigDict(strict=True, extra='ignore', frozen=True)


class Mensaje(Contrato):
    """Confirmación de operaciones: mensaje es el texto enviado por el backend."""
    mensaje: str = Field(min_length=1)
