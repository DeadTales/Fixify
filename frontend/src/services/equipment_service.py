"""Operaciones del módulo de equipos; mantiene el contrato actual de API."""
from services.api_client import ModuleService
from models.base import Mensaje
from models.equipment import Equipo, EquipoCrear, EquipoRegistrado


class EquipmentService(ModuleService):
    """Consulta y registra equipos asociados a un cliente."""

    async def listar(self) -> list[Equipo]:
        """Retorna equipos mediante GET /equipos/."""
        return await self._list('/equipos/', Equipo)

    async def crear(
        self,
        tipo,
        marca,
        modelo,
        problema_reportado,
        client_id,
        numero_serie=None,
    ) -> EquipoRegistrado:
        """tipo/marca/modelo: equipo; problema_reportado: falla; client_id: dueño; numero_serie: opcional."""

        entrada = self._parse(EquipoCrear, {
            'tipo': tipo, 'marca': marca, 'modelo': modelo,
            'problema_reportado': problema_reportado, 'client_id': client_id,
            'numero_serie': numero_serie or None,
        }, entrada=True)
        data = await self.api.request('POST', '/equipos/', json=entrada.model_dump())

        return self._parse(EquipoRegistrado, data)


    async def editar(self, record_id, **values) -> Equipo:
        entrada = self._parse(EquipoCrear, {**values, "numero_serie": values.get("numero_serie") or None}, entrada=True)
        data = await self.api.request('PUT', f'/equipos/{record_id}', json=entrada.model_dump())
        return self._parse(Equipo, data)

    async def eliminar(self, record_id) -> Mensaje:
        data = await self.api.request('DELETE', f'/equipos/{record_id}')
        return self._parse(Mensaje, data)
