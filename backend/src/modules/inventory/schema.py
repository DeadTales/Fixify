from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime

class MaterialCreate(BaseModel):
    clave: Optional[str] = None
    descripcion: str
    unidad: Optional[str] = None
    existencia_actual: int = Field(default=0, ge=0, description="La existencia disponible debe ser mayor o igual a 0")
    stock_minimo: int = Field(default=0, ge=0, description="El stock mínimo debe ser mayor o igual a 0")

class MaterialUpdate(BaseModel):
    clave: Optional[str] = None
    descripcion: Optional[str] = None
    unidad: Optional[str] = None
    existencia_actual: Optional[int] = Field(default=None, ge=0, description="La existencia disponible debe ser mayor o igual a 0")
    stock_minimo: Optional[int] = Field(default=None, ge=0, description="El stock mínimo debe ser mayor o igual a 0")

class MaterialResponse(BaseModel):
    id_material: int
    clave: Optional[str] = None
    descripcion: str
    unidad: Optional[str] = None
    existencia_actual: int
    stock_minimo: int

    @computed_field
    @property
    def bajo_stock(self) -> bool:
        """Compara si la existencia actual está en el umbral de alerta."""
        return self.existencia_actual <= self.stock_minimo

    class Config:
        from_attributes = True

class ConsumoCreate(BaseModel):
    id_orden: int
    id_material: int
    cantidad_utilizada: int = Field(gt=0, description="La cantidad utilizada debe ser mayor a 0")
    id_usuario: Optional[int] = None

class ConsumoResponse(BaseModel):
    id_consum: int
    id_orden: int
    id_material: int
    cantidad_utilizada: int
    id_usuario: Optional[int] = None
    material_descripcion: Optional[str] = None
    unidad: Optional[str] = None
    alerta_stock_bajo: Optional[str] = None  # Nuevo campo para notificar al usuario

    class Config:
        from_attributes = True
class StockAlertResponse(BaseModel):
    id_alerta: int
    id_material: int
    existencia_actual: int
    stock_minimo: int
    fecha_alerta: datetime
    material_descripcion: Optional[str] = None

    class Config:
        from_attributes = True