from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.conexion import get_db
from src.modules.auth.dependencies import verificar_rol_admin
from src.modules.users.repository import user_repository
# Esquemas públicos: validan entradas y excluyen hashes de las respuestas.
from src.modules.users.schema import UserCreate, UserUpdateRole, UserResponse, UserUpdate
from fastapi import HTTPException


# Al poner la dependencia aquí, TODOS los endpoints de este archivo exigen ser Admin
router = APIRouter(
    prefix="/usuarios",
    tags=["Gestión de Usuarios"],
    dependencies=[Depends(verificar_rol_admin)]
)
@router.patch("/{user_id}/habilitar")
def habilitar_cuenta(user_id: int, db: Session = Depends(get_db)):
    """user_id: cuenta a activar; db: sesión inyectada; 404 si no existe."""
    # Ejecutamos la función del repositorio
    usuario = user_repository.habilitar_usuario(db, user_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"mensaje": f"La cuenta de {usuario.username} ha sido habilitada para acceder al sistema."}
@router.patch("/{user_id}/inhabilitar")
def inhabilitar_cuenta(user_id: int, db: Session = Depends(get_db)):
    """user_id: cuenta a desactivar; conserva el registro y su rol."""
    # Ejecutamos la función del repositorio para bloquear el acceso
    usuario = user_repository.inhabilitar_usuario(db, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"mensaje": f"La cuenta de {usuario.username} ha sido inhabilitada. Su acceso fue bloqueado pero la información se conservó."}
@router.patch("/{user_id}/rol")
def actualizar_rol(user_id: int, nuevo_rol: UserUpdateRole, db: Session = Depends(get_db)):
    """user_id: cuenta; nuevo_rol: código de rol validado; db: sesión actual."""
    # Ejecutamos la función del repositorio para actualizar el rol
    usuario = user_repository.actualizar_rol(db, user_id, nuevo_rol.role)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"mensaje": f"El rol de {usuario.username} ha sido actualizado a {usuario.role}."}
@router.post("/")
def crear_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    """usuario: datos de alta; db: sesión; devuelve el nombre confirmado."""
    # Solo un administrador con token válido puede llegar a ejecutar esto
    nuevo_usuario = user_repository.create(db, usuario)
    return {"mensaje": "Usuario creado con éxito", "usuario": nuevo_usuario.username}

@router.get("/", response_model=list[UserResponse])
def obtener_usuarios(db: Session = Depends(get_db)):
    """db: sesión actual; UserResponse limita la salida a los campos públicos."""
    # Solo un administrador puede ver la lista de empleados
    return user_repository.get_all(db)


@router.put('/{user_id}', response_model=UserResponse)
def editar_usuario(user_id: int, values: UserUpdate, db: Session = Depends(get_db)):
    """Edita nombre y rol sin modificar contraseña, actividad ni historial."""
    return user_repository.update(db, user_id, values)
