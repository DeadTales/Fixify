from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.conexion import get_db
from src.shared.security import verificar_rol_admin
from src.modules.users.repository import user_repository
# Asumiendo que tienes tus esquemas Pydantic en schemas.py
from src.modules.users.schema import UserCreate, UserUpdateRole
from fastapi import HTTPException


# Al poner la dependencia aquí, TODOS los endpoints de este archivo exigen ser Admin
router = APIRouter(
    prefix="/usuarios",
    tags=["Gestión de Usuarios"],
    dependencies=[Depends(verificar_rol_admin)] 
)
@router.patch("/{user_id}/habilitar")
def habilitar_cuenta(user_id: int, db: Session = Depends(get_db)):
    # Ejecutamos la función del repositorio
    usuario = user_repository.habilitar_usuario(db, user_id)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return {"mensaje": f"La cuenta de {usuario.username} ha sido habilitada para acceder al sistema."}
@router.patch("/{user_id}/inhabilitar")
def inhabilitar_cuenta(user_id: int, db: Session = Depends(get_db)):
    # Ejecutamos la función del repositorio para bloquear el acceso
    usuario = user_repository.inhabilitar_usuario(db, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return {"mensaje": f"La cuenta de {usuario.username} ha sido inhabilitada. Su acceso fue bloqueado pero la información se conservó."}
@router.patch("/{user_id}/rol")
def cambiar_rol_usuario(
    user_id: int, 
    datos_rol: UserUpdateRole, 
    db: Session = Depends(get_db)
):
    # Como el archivo está protegido con verificar_rol_admin, 
    # solo un administrador puede ejecutar esta línea de código.
    usuario = user_repository.actualizar_rol(db, user_id, datos_rol.role)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return {
        "mensaje":"El rol del usuario {usuario.username} ha sido actualizado exitosamente a: {usuario.role}"
    }
@router.patch("/{user_id}/rol")
def actualizar_rol(user_id: int, nuevo_rol: UserUpdateRole, db: Session = Depends(get_db)):
    # Ejecutamos la función del repositorio para actualizar el rol
    usuario = user_repository.actualizar_rol(db, user_id, nuevo_rol.role)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return {"mensaje": f"El rol de {usuario.username} ha sido actualizado a {usuario.role}."}
@router.post("/")
def crear_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    # Solo un administrador con token válido puede llegar a ejecutar esto
    nuevo_usuario = user_repository.create(db, usuario)
    return {"mensaje": "Usuario creado con éxito", "usuario": nuevo_usuario.username}

@router.get("/")
def obtener_usuarios(db: Session = Depends(get_db)):
    # Solo un administrador puede ver la lista de empleados
    return user_repository.get_all(db)