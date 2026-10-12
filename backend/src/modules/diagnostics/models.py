from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from src.database.conexion import Base

class DiagnosticModel(Base):
    __tablename__ = "diagnosticos"
    __table_args__ = {'extend_existing': True}

    id_diagnostico = Column("id_diagnostico", Integer, primary_key=True, index=True, autoincrement=True)
    id_orden = Column("id_orden", Integer, ForeignKey("ordenes_servicio.id_orden"), nullable=False, unique=True)
    descripcion = Column("descripcion", Text, nullable=False)
    fecha_registro = Column("fecha_registro", DateTime(timezone=True), server_default=func.now())