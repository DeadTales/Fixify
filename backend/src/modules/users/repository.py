from sqlalchemy.orm import Session
from typing import Optional
from src.shared.base_repository import BaseRepository
from src.modules.users.model import User
from src.modules.users.schema import UserCreate, UserUpdate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Capa de persistencia para la entidad User.
    Al heredar de BaseRepository, ya tiene los métodos: 
    get_by_id, get_multi, create y remove.
    """
    
    # Agregamos consultas específicas que solo necesita este módulo
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Busca un usuario por su nombre de usuario en PostgreSQL."""
        return db.query(self.model).filter(self.model.username == username).first()

# Instanciamos el repositorio para importarlo y usarlo en las rutas
user_repository = UserRepository(User)