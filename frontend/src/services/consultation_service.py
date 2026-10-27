"""Consulta pública de una reparación sin crear una sesión de empleado."""
from models.consultation import ConsultaServicio, EstadoServicioPublico
from services.api_client import ModuleService


class ConsultationService(ModuleService):
    """Envía folio y teléfono; nunca solicita detalles internos de la orden."""

    async def consultar(self, folio, telefono) -> EstadoServicioPublico:
        entrada = self._parse(
            ConsultaServicio,
            {'folio': folio, 'telefono': telefono},
            entrada=True,
        )
        data = await self.api.request(
            'POST',
            '/consulta/servicio',
            authenticated=False,
            json=entrada.model_dump(),
        )
        return self._parse(EstadoServicioPublico, data)
