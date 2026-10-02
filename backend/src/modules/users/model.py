"""Usuario SQL: aliases conservan username/id/hash del contrato público."""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, true
from sqlalchemy.orm import relationship
from src.database.conexion import Base
from src.modules.roles.model import Role


class User(Base):
    __tablename__ = 'usuarios'
    id = Column('id_usuario', Integer, primary_key=True, autoincrement=True)
    id_rol = Column(Integer, ForeignKey('roles.id_rol'), nullable=True)
    username = Column('nombre', String(150), nullable=False)
    correo = Column(String(100), unique=True, nullable=True)
    hashed_password = Column('contrasena_hash', String(255), nullable=False)
    # Nombre físico en Supabase; is_active conserva el contrato del frontend.
    is_active = Column('is_active', Boolean, nullable=False, default=True, server_default=true())
    rol = relationship(Role, lazy='joined')

    @property
    def role(self):
        """Código de permisos derivado de la fila roles, no de otra columna."""
        return self.rol.code if self.rol else 'sin_rol'
