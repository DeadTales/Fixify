"""Contrato de personal, alta y cambios de rol; nunca conserva hashes."""
from pydantic import Field
from models.base import Contrato, Mensaje, Rol


class UsuarioCrear(Contrato):
    """username/password: credenciales; role: rol autorizado de dominio."""
    username: str = Field(min_length=4, max_length=50)
    password: str = Field(min_length=6, repr=False)
    role: Rol = 'tecnico'


class Usuario(Contrato):
    """Registro público: ID, nombre de cuenta, rol y estado de acceso."""
    id: int = Field(gt=0)
    username: str
    role: Rol
    is_active: bool


class RolActualizar(Contrato):
    """role: nuevo rol de la cuenta seleccionada."""
    role: Rol


class UsuarioRegistrado(Mensaje):
    """usuario: username confirmado por POST /usuarios/."""
    usuario: str
