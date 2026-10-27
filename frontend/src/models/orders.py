"""Contratos de órdenes, diagnóstico y trabajo técnico de Fixify."""
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from models.base import Contrato


EstadoOrden = Literal['Recibido', 'En revisión', 'Reparando', 'Listo', 'Entregado']
ESTADOS_ORDEN: tuple[EstadoOrden, ...] = (
    'Recibido', 'En revisión', 'Reparando', 'Listo', 'Entregado',
)


class OrdenCrear(Contrato):
    """Datos mínimos para recibir un equipo y abrir su orden."""
    id_cliente: int = Field(gt=0)
    id_equipo: int = Field(gt=0)
    id_tecnico: int | None = Field(default=None, gt=0)


class TecnicoAsignar(Contrato):
    id_tecnico: int = Field(gt=0)


class EstadoActualizar(Contrato):
    nuevo_estado: EstadoOrden


class Orden(Contrato):
    """Orden pública usada en listados y respuestas de mutaciones."""
    id_orden: int = Field(gt=0)
    folio: str | None = None
    id_equipo: int = Field(gt=0)
    id_cliente: int = Field(gt=0)
    id_tecnico: int | None = Field(default=None, gt=0)
    estado: EstadoOrden
    fecha_recepcion: str | None = None
    fecha_entrega: str | None = None
    causa: str | None = None
    acciones: str | None = None

    @field_validator('folio')
    @classmethod
    def validar_folio(cls, value):
        if value is not None and not value.strip():
            raise ValueError('El folio no puede estar vacío.')
        return value


class DiagnosticoCrear(Contrato):
    model_config = ConfigDict(strict=True, str_strip_whitespace=True)
    id_orden: int = Field(gt=0)
    descripcion: str = Field(min_length=5)


class Diagnostico(Contrato):
    id_diagnostico: int = Field(gt=0)
    id_orden: int = Field(gt=0)
    descripcion: str
    fecha_registro: str | None = None


class ActividadCrear(Contrato):
    model_config = ConfigDict(strict=True, str_strip_whitespace=True)
    trabajo_realizado: str = Field(min_length=3)
    solucion: str | None = Field(default=None, min_length=3)


class Actividad(Contrato):
    id_actividad: int = Field(gt=0)
    id_orden: int = Field(gt=0)
    trabajo_realizado: str
    solucion: str | None = None
    fecha_registro: str | None = None


class ResolucionCrear(Contrato):
    model_config = ConfigDict(strict=True, str_strip_whitespace=True)
    causa: str = Field(min_length=3)
    acciones: str = Field(min_length=3)
    estado_final: EstadoOrden


class HistorialEstado(Contrato):
    id_historial: int = Field(gt=0)
    id_orden: int = Field(gt=0)
    id_usuario: int = Field(gt=0)
    estado_anterior: str | None = None
    estado_nuevo: EstadoOrden
    fecha_cambio: str | None = None


class AsignacionTecnico(Contrato):
    """Cambio de responsable conservado por Supabase para auditoria."""
    id_asignacion: int = Field(gt=0)
    id_orden: int = Field(gt=0)
    id_usuario: int = Field(gt=0)
    id_tecnico_anterior: int | None = Field(default=None, gt=0)
    id_tecnico_nuevo: int = Field(gt=0)
    fecha_cambio: str | None = None


class DetalleOrden(Contrato):
    orden: Orden
    historial: list[HistorialEstado] = Field(default_factory=list)
    asignaciones: list[AsignacionTecnico] = Field(default_factory=list)
