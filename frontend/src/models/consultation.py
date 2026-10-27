"""Datos públicos para consultar el avance de una reparación."""
from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from models.base import Contrato


EstadoOrden = Literal['Recibido', 'En revisión', 'Reparando', 'Listo', 'Entregado']


class ConsultaServicio(Contrato):
    """Identificación y verificación mínima solicitada al cliente."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True, extra='ignore', frozen=True)
    folio: str = Field(min_length=3, max_length=50)
    telefono: str = Field(min_length=8, max_length=20)

    @field_validator('folio')
    @classmethod
    def normalizar_folio(cls, value):
        return value.upper()

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, value):
        if any(char not in '0123456789+()- . ' for char in value):
            raise ValueError('Teléfono inválido')
        if not 8 <= sum(char.isdigit() for char in value) <= 15:
            raise ValueError('Teléfono inválido')
        return value


class EstadoServicioPublico(Contrato):
    """Respuesta que excluye datos personales y notas técnicas."""

    folio: str
    estado: EstadoOrden
    equipo: str
    actualizadoEn: datetime

    @field_validator('actualizadoEn', mode='before')
    @classmethod
    def parse_actualizacion(cls, value):
        """Convierte el formato ISO recibido por JSON a una fecha verificable."""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value
