"""Contrato de clientes: datos para alta, registro consultado y confirmación."""
from pydantic import Field
from models.base import Contrato, Mensaje


class ClienteCrear(Contrato):
    """nombre/telefono: obligatorios; correo: contacto opcional."""
    nombre: str = Field(min_length=2, max_length=100)
    telefono: str = Field(min_length=8, max_length=20)
    correo: str | None = None


class Cliente(Contrato):
    """Registro leído; id es el identificador API, no el nombre físico de columna."""
    id: int = Field(gt=0)
    nombre: str
    telefono: str
    correo: str | None = None


class ClienteRegistrado(Mensaje):
    """Confirmación de alta; cliente contiene el registro persistido."""
    cliente: Cliente
