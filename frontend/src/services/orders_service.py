"""Operaciones HTTP del ciclo de vida de órdenes de servicio."""
from models.orders import (
    Actividad, ActividadCrear, DetalleOrden, Diagnostico, DiagnosticoCrear,
    EstadoActualizar, EstadoOrden, Orden, OrdenCrear, ResolucionCrear,
    TecnicoAsignar,
)
from models.users import Usuario
from services.api_client import ModuleService


class OrdersService(ModuleService):
    """Mantiene rutas y validación de órdenes fuera de los widgets Tk."""

    async def listar(self, **filtros) -> list[Orden]:
        """Consulta órdenes; omite filtros vacíos para conservar una URL limpia."""
        params = {name: value for name, value in filtros.items()
                  if value not in (None, '')}
        return await self._list('/ordenes/', Orden, params=params or None)

    async def crear(self, id_cliente, id_equipo, id_tecnico=None) -> Orden:
        entrada = self._parse(OrdenCrear, {
            'id_cliente': id_cliente,
            'id_equipo': id_equipo,
            'id_tecnico': id_tecnico,
        }, entrada=True)
        data = await self.api.request('POST', '/ordenes/', json=entrada.model_dump())
        return self._parse(Orden, data)

    async def detalle(self, id_orden) -> DetalleOrden:
        data = await self.api.request('GET', f'/ordenes/{id_orden}')
        return self._parse(DetalleOrden, data)

    async def listar_tecnicos(self) -> list[Usuario]:
        return await self._list('/usuarios/tecnicos', Usuario)

    async def asignar(self, id_orden, id_tecnico) -> Orden:
        entrada = self._parse(TecnicoAsignar, {'id_tecnico': id_tecnico}, entrada=True)
        data = await self.api.request(
            'PATCH', f'/ordenes/{id_orden}/tecnico',
            json=entrada.model_dump(),
        )
        return self._parse(Orden, data)

    async def diagnosticar(self, id_orden, descripcion) -> Diagnostico:
        entrada = self._parse(DiagnosticoCrear, {
            'id_orden': id_orden, 'descripcion': descripcion,
        }, entrada=True)
        data = await self.api.request(
            'POST', '/diagnosticos/', json=entrada.model_dump(),
        )
        return self._parse(Diagnostico, data)

    async def obtener_diagnostico(self, id_orden) -> Diagnostico:
        data = await self.api.request('GET', f'/diagnosticos/orden/{id_orden}')
        return self._parse(Diagnostico, data)

    async def cambiar_estado(self, id_orden: int, nuevo_estado: EstadoOrden) -> Orden:
        # El backend toma el actor del JWT para que el historial no pueda
        # atribuirse a otro usuario desde la interfaz.
        entrada = self._parse(
            EstadoActualizar, {'nuevo_estado': nuevo_estado}, entrada=True,
        )
        data = await self.api.request(
            'PATCH', f'/ordenes/{id_orden}/estado',
            json=entrada.model_dump(),
        )
        return self._parse(Orden, data)

    async def registrar_actividad(
        self, id_orden, trabajo_realizado, solucion=None,
    ) -> Actividad:
        entrada = self._parse(ActividadCrear, {
            'trabajo_realizado': trabajo_realizado,
            'solucion': solucion or None,
        }, entrada=True)
        data = await self.api.request(
            'POST', f'/ordenes/{id_orden}/actividades',
            json=entrada.model_dump(),
        )
        return self._parse(Actividad, data)

    async def listar_actividades(self, id_orden) -> list[Actividad]:
        return await self._list(f'/ordenes/{id_orden}/actividades', Actividad)

    async def resolver(self, id_orden, causa, acciones, estado_final='Listo') -> Orden:
        entrada = self._parse(ResolucionCrear, {
            'causa': causa, 'acciones': acciones, 'estado_final': estado_final,
        }, entrada=True)
        data = await self.api.request(
            'PATCH', f'/ordenes/{id_orden}/resolver',
            json=entrada.model_dump(),
        )
        return self._parse(Orden, data)

    async def entregar(self, id_orden) -> Orden:
        data = await self.api.request('PATCH', f'/ordenes/{id_orden}/entregar')
        return self._parse(Orden, data)
