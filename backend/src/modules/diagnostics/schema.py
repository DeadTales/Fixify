from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DiagnosticCreate(BaseModel):
    id_orden: int
    descripcion: str

class DiagnosticResponse(BaseModel):
    id_diagnostico: int
    id_orden: int
    descripcion: str
    fecha_registro: Optional[datetime] = None

    class Config:
        from_attributes = True