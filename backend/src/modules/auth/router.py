from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.database.conexion import get_db
from src.modules.users.repository import user_repository
from src.shared.security import verify_password, create_access_token


router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Buscar al usuario en Supabase por su nombre de usuario
    user = user_repository.get_by_username(db, username=form_data.username)
    
    # 2. Validar que el usuario exista y la contraseña sea correcta
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 1. Buscar al usuario
    user = user_repository.get_by_username(db, username=form_data.username)
    
    # 2. Validar que exista y la contraseña coincida
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    # 3. EL NUEVO CANDADO: Verificar si la cuenta está habilitada
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta deshabilitada. Contacte al administrador.")
    # 3. Si es correcto, generar el token JWT incluyendo su rol
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    # 4. Responder al frontend
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "message": "Ingreso exitoso"
    }