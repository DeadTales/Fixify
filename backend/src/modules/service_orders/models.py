from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database.conexion import Base

class ServiceOrderModel(Base):
    __tablename__ = "ordenes_servicio"
    __table_args__ = {'extend_existing': True}

    id_orden = Column(Integer, primary_key=True, index=True)
    folio = Column(String(50), unique=True, index=True, nullable=True)
    id_equipo = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=False)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    id_tecnico = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    estado = Column(String(50), default="Recibido")
    fecha_recepcion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_entrega = Column(DateTime(timezone=True), nullable=True)