"""Entidades restantes del SQL local; no implementan endpoints de mantenimiento."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, text
from src.database.conexion import Base


class Material(Base):
    """Material: descripción, existencias y mínimo de inventario."""
    __tablename__ = 'materiales'
    id_material = Column(Integer, primary_key=True, autoincrement=True)
    descripcion = Column(String(200), nullable=False)
    existencia_actual = Column(Integer, server_default=text('0'))
    stock_minimo = Column(Integer, server_default=text('0'))


class ServiceOrder(Base):
    """Orden: folio, propietario, equipo, técnico, estado y fechas."""
    __tablename__ = 'ordenes_servicio'
    id_orden = Column(Integer, primary_key=True, autoincrement=True)
    folio = Column(String(50), unique=True, nullable=False)
    id_equipo = Column(Integer, ForeignKey('equipos.id_equipo'), nullable=False)
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente'), nullable=False)
    id_tecnico = Column(Integer, ForeignKey('usuarios.id_usuario'))
    estado = Column(String(50), nullable=False)
    fecha_recepcion = Column(DateTime, server_default=func.current_timestamp())
    fecha_entrega = Column(DateTime)


class Diagnosis(Base):
    """Diagnóstico asociado a una orden y su fecha de registro."""
    __tablename__ = 'diagnosticos'
    id_diagnostico = Column(Integer, primary_key=True, autoincrement=True)
    id_orden = Column(Integer, ForeignKey('ordenes_servicio.id_orden'), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha_registro = Column(DateTime, server_default=func.current_timestamp())


class RepairActivity(Base):
    """Actividad y solución documentadas durante una reparación."""
    __tablename__ = 'actividades_reparacion'
    id_actividad = Column(Integer, primary_key=True, autoincrement=True)
    id_orden = Column(Integer, ForeignKey('ordenes_servicio.id_orden'), nullable=False)
    trabajo_realizado = Column(Text, nullable=False)
    solucion = Column(Text)
    fecha_registro = Column(DateTime, server_default=func.current_timestamp())


class MaterialConsumption(Base):
    """Cantidad de un material utilizada en una orden."""
    __tablename__ = 'consumos_material'
    id_consumo = Column(Integer, primary_key=True, autoincrement=True)
    id_orden = Column(Integer, ForeignKey('ordenes_servicio.id_orden'), nullable=False)
    id_material = Column(Integer, ForeignKey('materiales.id_material'), nullable=False)
    cantidad_utilizada = Column(Integer, nullable=False)


class StateHistory(Base):
    """Cambio de estado: orden, usuario, valores anterior/nuevo y fecha."""
    __tablename__ = 'historial_estados'
    id_historial = Column(Integer, primary_key=True, autoincrement=True)
    id_orden = Column(Integer, ForeignKey('ordenes_servicio.id_orden'), nullable=False)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    estado_anterior = Column(String(50))
    estado_nuevo = Column(String(50), nullable=False)
    fecha_cambio = Column(DateTime, server_default=func.current_timestamp())
