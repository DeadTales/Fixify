"""Operaciones de autenticación; no modifica widgets ni guarda contraseñas."""
from services.api_client import ModuleService
from models.auth import Login, Sesion


class AuthService(ModuleService):
    """Solicita credenciales de sesión al backend."""

    async def login(self, username, password) -> Sesion:
        """username/password: credenciales; retorna token y rol validados."""

        entrada = self._parse(
            Login,
            {'username': username, 'password': password},
            entrada=True,
        )
        data = await self.api.request(
            'POST',
            '/auth/login',
            authenticated=False,
            data=entrada.model_dump(),
        )

        # La UI guarda el token solo si aún existe la ventana que pidió el login.
        return self._parse(Sesion, data)
