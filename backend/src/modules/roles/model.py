"""Roles físicos del SQL y traducción al contrato de permisos de la API."""
import unicodedata
from sqlalchemy import Column, Integer, String
from src.database.conexion import Base


class Role(Base):
    __tablename__ = 'roles'
    id = Column('id_rol', Integer, primary_key=True, autoincrement=True)
    nombre_rol = Column(String(50), nullable=False)

    @property
    def code(self):
        """Convierte etiquetas del SQL, incluidas las de prueba, al rol de dominio."""
        name = ''.join(c for c in unicodedata.normalize('NFD', self.nombre_rol.lower())
                       if not unicodedata.combining(c))
        if name.startswith('admin'):
            return 'admin'
        if name.startswith('tecnico'):
            return 'tecnico'
        if name.startswith('recep'):
            return 'recepcion'
        return 'sin_rol'
