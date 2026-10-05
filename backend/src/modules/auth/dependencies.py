"""Permisos basados en el estado actual de la cuenta, incluso con JWT antiguos."""
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from src.config.settings import settings
from src.database.conexion import get_db
from src.modules.users.repository import user_repository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def verificar_usuario_autenticado(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'],
                             options={'require': ['exp', 'sub']})
        if not isinstance(payload['sub'], str) or not payload['sub']:
            raise jwt.InvalidTokenError()
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='Token inválido o expirado',
                            headers={'WWW-Authenticate': 'Bearer'})
    user = user_repository.get_by_username(db, payload['sub'])
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail='La sesión ya no está autorizada.',
                            headers={'WWW-Authenticate': 'Bearer'})
    if user.role not in ('admin', 'recepcion', 'tecnico'):
        raise HTTPException(status_code=403, detail='La cuenta no tiene un rol autorizado.')
    return {**payload, 'role': user.role, 'user_id': user.id}


def verificar_rol_admin(payload: dict = Depends(verificar_usuario_autenticado)):
    if payload['role'] != 'admin':
        raise HTTPException(status_code=403, detail='Operación exclusiva para administradores.')
    return payload


def verificar_rol_tecnico_o_superior(payload: dict = Depends(verificar_usuario_autenticado)):
    return payload


def verificar_rol_recepcion_o_admin(payload: dict = Depends(verificar_usuario_autenticado)):
    if payload['role'] not in ('admin', 'recepcion'):
        raise HTTPException(status_code=403, detail='Acceso exclusivo para Recepción y Administración.')
    return payload
