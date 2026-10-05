from pydantic import BaseModel, Field, ConfigDict

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=4,
        max_length=50,
        description="El nombre de usuario es obligatorio y debe tener al menos 4 caracteres"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="La contraseña es obligatoria y debe tener al menos 6 caracteres"
    )
    role: str = Field(
        default="tecnico",
        pattern="^(admin|tecnico|recepcion)$",
        description="Rol del usuario: admin, tecnico o recepcion"
    )

class UserUpdateRole(BaseModel):
    role: str = Field(
        ...,
        pattern="^(admin|tecnico|recepcion)$",
        description="Nuevo rol a asignar"
    )

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Edición pública de nombre y rol; no modifica la contraseña."""
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = Field(..., min_length=4, max_length=50)
    role: str = Field(..., pattern='^(admin|tecnico|recepcion)$')
