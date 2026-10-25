from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database.conexion import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database.conexion import Base

class MaterialModel(Base):
    __tablename__ = "materiales"
    __table_args__ = {'extend_existing': True}

    id_material = Column(Integer, primary_key=True, index=True, autoincrement=True)
    clave = Column(String(50), unique=True, index=True, nullable=True)
    descripcion = Column(String(255), nullable=False)
    unidad = Column(String(50), nullable=True)
    existencia_actual = Column(Integer, default=0, nullable=False)
    stock_minimo = Column(Integer, default=0, nullable=False)

class ConsumoMaterialModel(Base):
    __tablename__ = "consumos_material"
    __table_args__ = {'extend_existing': True}

    id_consum = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_orden = Column(Integer, ForeignKey("ordenes_servicio.id_orden"), nullable=False)
    id_material = Column(Integer, ForeignKey("materiales.id_material"), nullable=False)
    cantidad_utilizada = Column(Integer, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    fecha_movimiento = Column(DateTime(timezone=True), server_default=func.now())

class StockAlertModel(Base):
    __tablename__ = "historial_alertas_stock"
    __table_args__ = {'extend_existing': True}

    id_alerta = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_material = Column(Integer, ForeignKey("materiales.id_material"), nullable=False)
    existencia_actual = Column(Integer, nullable=False)
    stock_minimo = Column(Integer, nullable=False)
    fecha_alerta = Column(DateTime(timezone=True), server_default=func.now())