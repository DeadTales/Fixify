from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# Esquema para Registrar un Cliente
class ClientCreate(BaseModel):
    # OBLIGATORIO: Usamos Field(...) y un largo mínimo
    nombre: str = Field(..., min_length=2, max_length=100, description="El nombre es obligatorio")
    telefono: str = Field(..., min_length=8, max_length=20, description="Teléfono de contacto obligatorio")
    
    # OPCIONAL: Usamos Optional[tipo] = None
    correo: Optional[EmailStr] = Field(None, description="Correo electrónico opcional pero con formato válido si se proporciona")
    direccion: Optional[str] = Field(None, max_length=250, description="Dirección opcional")

# Esquema de respuesta para el cliente
class ClientResponse(BaseModel):
    id: int
    nombre: str
    telefono: str
    correo: Optional[str] = None
    direccion: Optional[str] = None

    class Config:
        from_attributes = True
class ClientMessageResponse(BaseModel):
    mensaje: str