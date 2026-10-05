"""Credenciales de entrada y sesión devuelta por /auth/login."""
from typing import Literal
from pydantic import Field
from models.base import Contrato, Rol


class Login(Contrato):
    """username/password: credenciales; password se oculta en la representación."""
    username: str = Field(min_length=1)
    password: str = Field(min_length=1, repr=False)


class Sesion(Contrato):
    """access_token: JWT; token_type: esquema Bearer; role: permisos; message: confirmación."""
    access_token: str = Field(min_length=1, repr=False)
    token_type: Literal['bearer']
    role: Rol
    message: str | None = None
