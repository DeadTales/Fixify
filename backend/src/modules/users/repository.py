from sqlalchemy.orm import Session
from src.modules.users.model import User
from src.modules.users.schema import UserCreate
from src.shared.security import get_password_hash

class UserRepository:
    def get_by_username(self, db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    def get_all(self, db: Session):
        return db.query(User).all()

    def create(self, db: Session, user_in: UserCreate):
        # 1. Encriptamos la contraseña con la función que hicimos antes
        hashed_pw = get_password_hash(user_in.password)
        
        # 2. Preparamos el objeto para la Base de Datos
        db_user = User(
            username=user_in.username,
            hashed_password=hashed_pw,
            role=user_in.role
        )
        
        # 3. Guardamos en Supabase
        db.add(db_user)
        db.commit()
        db.refresh(db_user) # Refrescamos para obtener el ID generado
        
        return db_user
    def habilitar_usuario(self, db: Session, user_id: int):
        # Buscamos al usuario por su ID
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = True  # Encendemos la cuenta
            db.commit()
            db.refresh(user)
        return user
    def inhabilitar_usuario(self, db: Session, user_id: int):
        # Buscamos al usuario por su ID
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False  # Apagamos la cuenta (Bloqueo de acceso)
            db.commit()
            db.refresh(user)
        return user  
    def actualizar_rol(self, db: Session, user_id: int, nuevo_rol: str):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.role = nuevo_rol  # Modificamos el perfil
            db.commit()
            db.refresh(user)
        return user
# Instancia lista para usarse en el router
user_repository = UserRepository()