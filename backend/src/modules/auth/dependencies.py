from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from src.config.settings import settings

# Le indica a FastAPI de dónde viene el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
def verificar_usuario_autenticado(token: str = Depends(oauth2_scheme)):
    """token: Bearer JWT; valida firma/expiración sin consultar estado actual en BD."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

def verificar_rol_admin(token: str = Depends(oauth2_scheme)):
    """token: JWT firmado; exige el rol admin almacenado al iniciar sesión."""
    try:
        # Abrimos el gafete (token) para leer su contenido
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        rol = payload.get("role")
        
        if rol != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operación denegada. Solo para administradores."
            )
        return payload # Devuelve los datos si todo está bien
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
def verificar_rol_tecnico_o_superior(token: str = Depends(oauth2_scheme)):
    """Permite el acceso a técnicos, administradores y recepción (prácticamente cualquier usuario activo)."""
    payload = verificar_usuario_autenticado(token)
    # Como todos los roles válidos entran, basta con que esté autenticado, 
    # pero puedes restringirlo explícitamente si lo deseas:
    if payload.get("role") not in ["admin", "tecnico", "recepcion"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado."
        )
    return payload

def verificar_rol_recepcion_o_admin(token: str = Depends(oauth2_scheme)):
    """Exclusivo para Recepción y Administración (ideal para registrar clientes, equipos u órdenes)."""
    payload = verificar_usuario_autenticado(token)
    
    if payload.get("role") not in ["admin", "recepcion"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso exclusivo para Recepción y Administración."
        )
    return payload
