"""Contrato de clientes: datos para alta, registro consultado y confirmación."""
from pydantic import field_validator, Field, ConfigDict
from models.base import Contrato, Mensaje


class ClienteCrear(Contrato):
    model_config = ConfigDict(str_strip_whitespace=True)
    """nombre/telefono: obligatorios; correo: contacto opcional."""
    nombre: str = Field(min_length=2, max_length=100)
    telefono: str = Field(min_length=8, max_length=20)
    correo: str | None = None


    @field_validator('telefono')
    @classmethod
    def validate_phone(cls, value):
        if any(char not in '0123456789+()- . ' for char in value) or not 8 <= sum(char.isdigit() for char in value) <= 15:
            raise ValueError('Ingrese un teléfono válido con entre 8 y 15 dígitos.')
        return value


class Cliente(Contrato):
    """Registro leído; id es el identificador API, no el nombre físico de columna."""
    id: int = Field(gt=0)
    nombre: str
    telefono: str
    correo: str | None = None


class ClienteRegistrado(Mensaje):
    """Confirmación de alta; cliente contiene el registro persistido."""
    cliente: Cliente
