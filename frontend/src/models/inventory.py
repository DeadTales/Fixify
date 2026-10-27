"""Contratos del catálogo, consumos y alertas de inventario."""
from datetime import datetime

from pydantic import Field, field_validator

from models.base import Contrato


class Material(Contrato):
    """Material disponible y su umbral configurado."""

    id_material: int = Field(gt=0)
    clave: str | None = None
    descripcion: str = Field(min_length=1)
    unidad: str | None = None
    existencia_actual: int = Field(ge=0)
    stock_minimo: int = Field(ge=0)
    bajo_stock: bool


class ConsumoMaterial(Contrato):
    """Movimiento de salida asociado a una orden."""

    id_consum: int = Field(gt=0)
    id_orden: int = Field(gt=0)
    id_material: int = Field(gt=0)
    cantidad_utilizada: int = Field(gt=0)
    # Supabase conserva este valor como texto y no declara una FK.
    id_usuario: str | None = None
    fecha_movimiento: str | None = None
    material_descripcion: str | None = None
    unidad: str | None = None
    alerta_stock_bajo: str | None = None


class AlertaStock(Contrato):
    """Evento histórico emitido al alcanzar el mínimo."""

    id_alerta: int = Field(gt=0)
    id_material: int = Field(gt=0)
    existencia_actual: int = Field(ge=0)
    stock_minimo: int = Field(ge=0)
    fecha_alerta: datetime | None = None
    material_descripcion: str | None = None

    @field_validator('fecha_alerta', mode='before')
    @classmethod
    def parse_fecha(cls, value):
        """HTTP entrega fechas ISO; el contrato conserva datetime internamente."""
        if value is None:
            return None
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value
