from sqlalchemy import Column, Integer, String, Text, ForeignKey
from src.database.conexion import Base

class Equipment(Base):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(50), nullable=False)        # Ej. Laptop, Celular, Consola
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    numero_serie = Column(String(100), nullable=True)
    problema_reportado = Column(Text, nullable=False)
    
    # Relación con el cliente que creamos antes
    client_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)