from sqlalchemy import Column, Integer, String, Text
from src.database.conexion import Base

class Client(Base):
    __tablename__ = "clientes"

    # AQUÍ ESTÁ EL CAMBIO: Le indicamos que el nombre real en Supabase es "id_cliente"
    id = Column("id_cliente", Integer, primary_key=True, index=True, autoincrement=True)
    
    # --- DATOS OBLIGATORIOS (nullable=False) ---
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False) # Obligatorio para contactar al taller
    
    # --- DATOS OPCIONALES (nullable=True) ---
    correo = Column(String(100), nullable=True)     # No todos los clientes usan correo
    direccion = Column(Text, nullable=True)         # Opcional