from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.modules.users.model import User
from src.modules.roles.model import Role
from src.modules.users.schema import UserCreate
from src.shared.security import get_password_hash


class UserRepository:
    """Persistencia de usuarios y catálogo de roles; cada cambio confirma la sesión."""
    def get_by_username(self, db: Session, username: str):
        """Busca por nombre de cuenta; también permite ingresar con correo."""
        return db.query(User).filter((User.username == username) | (User.correo == username)).first()

    def get_all(self, db: Session):
        """db: sesión actual; devuelve cuentas ordenadas por ID."""
        return db.query(User).order_by(User.id).all()

    def get_role(self, db: Session, code: str):
        """Localiza la etiqueta SQL que representa el rol de dominio."""
        role = next((role for role in db.query(Role).order_by(Role.id).all() if role.code == code), None)
        if role is None:
            raise HTTPException(status_code=409, detail='El rol solicitado no existe en el catálogo roles.')
        return role

    def create(self, db: Session, user_in: UserCreate):
        """user_in: credenciales y rol; guarda hash y FK, nunca contraseña plana."""
        if self.get_by_username(db, user_in.username):
            raise HTTPException(status_code=409, detail='El usuario ya existe.')
        db_user = User(username=user_in.username, hashed_password=get_password_hash(user_in.password),
                       rol=self.get_role(db, user_in.role))
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def habilitar_usuario(self, db: Session, user_id: int):
        """user_id: cuenta destino; guarda is_active=True sin cambiar su rol."""
        user = db.get(User, user_id)
        if user:
            user.is_active = True
            db.commit()
            db.refresh(user)
        return user

    def inhabilitar_usuario(self, db: Session, user_id: int):
        """user_id: cuenta destino; bloquea nuevos logins sin eliminar el usuario."""
        user = db.get(User, user_id)
        if user:
            user.is_active = False
            db.commit()
            db.refresh(user)
        return user

    def actualizar_rol(self, db: Session, user_id: int, nuevo_rol: str):
        """user_id: cuenta; nuevo_rol: código que se resuelve a una fila roles."""
        user = db.get(User, user_id)
        if user:
            user.rol = self.get_role(db, nuevo_rol)
            db.commit()
            db.refresh(user)
        return user


user_repository = UserRepository()
