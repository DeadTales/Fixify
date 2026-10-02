"""Rutas de administración de usuarios, independientes de las otras entidades."""
from services.api_client import ModuleService
from models.base import Mensaje
from models.users import Usuario, UsuarioCrear, UsuarioRegistrado, RolActualizar


class UsersService(ModuleService):
    """Operaciones de usuarios autorizadas por el backend para admin."""

    async def listar(self) -> list[Usuario]:
        """Retorna el personal registrado."""
        return await self._list('/usuarios/', Usuario)

    async def crear(self, username, password, role) -> UsuarioRegistrado:
        """username/password: credenciales; role: admin, tecnico o recepcion."""

        entrada = self._parse(UsuarioCrear, {
            'username': username, 'password': password, 'role': role,
        }, entrada=True)
        data = await self.api.request('POST', '/usuarios/', json=entrada.model_dump())

        return self._parse(UsuarioRegistrado, data)

    async def cambiar_rol(self, user_id, role) -> Mensaje:
        """user_id: cuenta destino; role: nuevo rol de dominio."""

        entrada = self._parse(RolActualizar, {'role': role}, entrada=True)
        data = await self.api.request(
            'PATCH',
            f'/usuarios/{user_id}/rol',
            json=entrada.model_dump(),
        )

        return self._parse(Mensaje, data)

    async def activar(self, user_id, activo=True) -> Mensaje:
        """user_id: cuenta destino; activo: habilitar o inhabilitar acceso."""

        action = 'habilitar' if activo else 'inhabilitar'
        data = await self.api.request('PATCH', f'/usuarios/{user_id}/{action}')

        return self._parse(Mensaje, data)
