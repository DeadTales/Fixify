from pydantic import BaseModel
from typing import Optional
from src.shared.base_schema import BaseSchema

# Lo que envía el cliente para crear un usuario (incluye la contraseña en texto plano)
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "recepcion"

# Lo que se puede actualizar
class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Lo que responde la API (Oculta la contraseña)
class UserResponse(BaseSchema):
    id: int
    username: str
    role: str
    is_active: bool