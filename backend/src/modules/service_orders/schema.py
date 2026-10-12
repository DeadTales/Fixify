from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OrderCreate(BaseModel):
    id_cliente: int
    id_equipo: int
    id_tecnico: Optional[int] = None
    estado: Optional[str] = "Recibido"

class OrderResponse(BaseModel):
    id_orden: int
    folio: Optional[str] = None
    id_equipo: int
    id_cliente: int
    id_tecnico: Optional[int] = None
    estado: str
    fecha_recepcion: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None

    class Config:
        from_attributes = True