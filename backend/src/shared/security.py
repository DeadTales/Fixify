from datetime import datetime, timedelta
import bcrypt
import jwt
from src.config.settings import settings
from fastapi import HTTPException

# bcrypt genera hashes unidireccionales; las contraseñas no se cifran de forma reversible.


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """plain_password: contraseña recibida; hashed_password: hash bcrypt almacenado."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    """password: contraseña a convertir en hash; máximo 72 bytes en UTF-8."""
    if len(password.encode('utf-8')) > 72:
        raise HTTPException(status_code=422, detail='La contraseña excede el límite de 72 bytes de bcrypt.')
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict) -> str:
    """data: claims de usuario/rol; firma un JWT HS256 con vigencia de ocho horas."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=8)
    to_encode.update({"exp": expire})
    
    # SECRET_KEY se carga desde DataBase.env mediante Settings.
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt
