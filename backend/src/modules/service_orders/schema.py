from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OrderCreate(BaseModel):
    id_cliente: int
    id_equipo: int
    id_tecnico: Optional[int] = None
    estado: Optional[str] = "Recibido"

class OrderResolutionUpdate(BaseModel):
    causa: str
    acciones: str
    estado_final: str

class OrderResponse(BaseModel):
    id_orden: int
    folio: Optional[str] = None
    id_equipo: int
    id_cliente: int
    id_tecnico: Optional[int] = None
    estado: str
    fecha_recepcion: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    causa: Optional[str] = None
    acciones: Optional[str] = None

class ActivityCreate(BaseModel):
    trabajo_realizado: str
    solucion: str

class ActivityResponse(BaseModel):
    id_actividad: int
    id_orden: int
    trabajo_realizado: str
    solucion: str
    fecha_registro: Optional[datetime] = None
    
class ConsumoMaterialCreate(BaseModel):
    id_material: int
    cantidad_utilizada: int

class ConsumoMaterialResponse(BaseModel):
    id_consum: int
    id_orden: int
    id_material: int
    cantidad_utilizada: int

class Config:
    from_attributes = True