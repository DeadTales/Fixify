"""Rutas de clientes y transformación de sus datos de entrada."""
from services.api_client import ModuleService
from models.base import Mensaje
from models.clients import Cliente, ClienteCrear, ClienteRegistrado


class ClientsService(ModuleService):
    """Consulta y registra clientes mediante la API."""

    async def listar(self) -> list[Cliente]:
        """Retorna los clientes permitidos para la sesión actual."""
        return await self._list('/clientes/', Cliente)

    async def crear(self, nombre, telefono, correo=None) -> ClienteRegistrado:
        """nombre/telefono: obligatorios; correo: dato opcional."""

        entrada = self._parse(ClienteCrear, {
            'nombre': nombre, 'telefono': telefono,
            'correo': correo or None,
        }, entrada=True)
        data = await self.api.request('POST', '/clientes/', json=entrada.model_dump())

        return self._parse(ClienteRegistrado, data)

    async def buscar(self, termino) -> list[Cliente]:
        """termino: parte del nombre o teléfono que se desea localizar."""
        return await self._list('/clientes/buscar', Cliente, params={'q': termino})


    async def editar(self, record_id, **values) -> Cliente:
        entrada = self._parse(ClienteCrear, {**values, "correo": values.get("correo") or None}, entrada=True)
        data = await self.api.request('PUT', f'/clientes/{record_id}', json=entrada.model_dump())
        return self._parse(Cliente, data)

    async def eliminar(self, record_id) -> Mensaje:
        data = await self.api.request('DELETE', f'/clientes/{record_id}')
        return self._parse(Mensaje, data)
