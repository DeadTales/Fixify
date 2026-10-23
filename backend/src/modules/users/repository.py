from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.modules.users.model import User
from src.modules.roles.model import Role
from src.modules.users.schema import UserCreate
from src.shared.security import get_password_hash
from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.modules.users.model import User, Role # Ajusta los imports según tus rutas reales

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

    def get_technicians(self, db: Session):
        """Filtra y devuelve únicamente a los usuarios que tienen el rol de técnico."""
        # 1. Obtenemos el objeto rol usando tu método existente (asumiendo que el código es 'tecnico')
        rol_tecnico = self.get_role(db, code="tecnico")
        
        # 2. Consultamos los usuarios que coincidan con ese id_rol de la base de datos
        return db.query(User).filter(User.id_rol == rol_tecnico.id).all()

    def create(self, db: Session, user_in: UserCreate):
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


    def update(self, db: Session, user_id: int, values):
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail='Usuario no encontrado')
        duplicate = db.query(User.id).filter(
            User.id != user_id,
            (User.username == values.username) | (User.correo == values.username)
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail='El usuario ya existe.')
        role = self.get_role(db, values.role)
        user.username = values.username
        user.rol = role
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail='La cuenta entra en conflicto con otro registro.')
        db.refresh(user)
        return user


user_repository = UserRepository()
