from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from src.config.settings import settings

# Motor para encriptar contraseñas usando el algoritmo bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña en texto plano del frontend con la encriptada en PostgreSQL."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Convierte una contraseña a su versión encriptada para guardarla en la BD."""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Genera el gafete digital (JWT) con una vigencia de 8 horas."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=8)
    to_encode.update({"exp": expire})
    
    # Firma el token usando la llave secreta de tu archivo .env
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt