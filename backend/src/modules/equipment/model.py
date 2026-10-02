from sqlalchemy import Column, Integer, String, Text, ForeignKey
from src.database.conexion import Base

class Equipment(Base):
    __tablename__ = "equipos"

    # Conservamos los atributos de la API y usamos los nombres físicos del diagrama.
    id = Column("id_equipo", Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(50), nullable=True)        # Ej. Laptop, Celular, Consola
    marca = Column(String(50), nullable=True)
    modelo = Column(String(50), nullable=True)
    numero_serie = Column(String(100), nullable=True)
    problema_reportado = Column("falla_reportada", Text, nullable=True)
    
    # Relación con el cliente que creamos antes
    client_id = Column("id_cliente", Integer, ForeignKey("clientes.id_cliente"), nullable=False)
