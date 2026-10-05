from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class EquipmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    tipo: str = Field(..., min_length=2, max_length=50, description="Tipo de aparato")
    marca: str = Field(..., min_length=2, max_length=50)
    modelo: str = Field(..., min_length=2, max_length=50)
    numero_serie: Optional[str] = Field(None, max_length=100)
    problema_reportado: str = Field(..., min_length=5, description="Falla descrita por el cliente")
    client_id: int = Field(..., gt=0, description="ID del cliente propietario")

class EquipmentResponse(BaseModel):
    id: int
    tipo: str
    marca: str
    modelo: str
    numero_serie: Optional[str] = None
    problema_reportado: str
    client_id: int

    class Config:
        from_attributes = True
