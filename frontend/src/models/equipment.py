"""Contrato de equipos; mantiene los nombres públicos de la API."""
from pydantic import Field
from models.base import Contrato, Mensaje


class EquipoCrear(Contrato):
    """Características, falla y client_id del propietario; serie opcional."""
    tipo: str = Field(min_length=2, max_length=50)
    marca: str = Field(min_length=2, max_length=50)
    modelo: str = Field(min_length=2, max_length=50)
    problema_reportado: str = Field(min_length=5)
    client_id: int = Field(gt=0)
    numero_serie: str | None = Field(default=None, max_length=100)


class Equipo(Contrato):
    """Registro consultado: id, características, falla y propietario."""
    id: int = Field(gt=0)
    tipo: str
    marca: str
    modelo: str
    problema_reportado: str
    client_id: int = Field(gt=0)
    numero_serie: str | None = None


class DetallesEquipo(Contrato):
    """Resumen del POST; usa id_interno/cliente_id según la respuesta actual."""
    id_interno: int = Field(gt=0)
    tipo: str
    marca: str
    modelo: str
    cliente_id: int = Field(gt=0)


class EquipoRegistrado(Mensaje):
    """Confirmación de alta: folio visual y resumen del equipo guardado."""
    folio: str = Field(min_length=1)
    detalles: DetallesEquipo
