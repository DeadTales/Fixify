from pydantic import field_validator, BaseModel, Field, ConfigDict, EmailStr
from typing import Optional

# Esquema para Registrar un Cliente
class ClientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    # OBLIGATORIO: Usamos Field(...) y un largo mínimo
    nombre: str = Field(..., min_length=2, max_length=100, description="El nombre es obligatorio")
    telefono: str = Field(..., min_length=8, max_length=20, description="Teléfono de contacto obligatorio")

    # OPCIONAL: Usamos Optional[tipo] = None
    correo: Optional[EmailStr] = Field(None, description="Correo electrónico opcional pero con formato válido si se proporciona")

# Esquema de respuesta para el cliente
    @field_validator('telefono')
    @classmethod
    def validate_phone(cls, value):
        if any(char not in '0123456789+()- . ' for char in value) or not 8 <= sum(char.isdigit() for char in value) <= 15:
            raise ValueError('Ingrese un teléfono válido con entre 8 y 15 dígitos.')
        return value


class ClientResponse(BaseModel):
    id: int
    nombre: str
    telefono: str
    correo: Optional[str] = None

    class Config:
        from_attributes = True
class ClientMessageResponse(BaseModel):
    mensaje: str

class ClientRegistered(BaseModel):
    mensaje: str
    cliente: ClientResponse
