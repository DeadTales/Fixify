from sqlalchemy import Column, Integer, String, Boolean
from src.database.conexion import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="recepcion", nullable=False) # Roles: admin, tecnico, recepcion
    is_active = Column(Boolean, default=True)