from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.conexion import get_db
from src.modules.service_orders.schema import OrderCreate, OrderResponse
from src.modules.service_orders.repository import service_order_repository

router = APIRouter(
    prefix="/ordenes",
    tags=["Gestión de Órdenes de Servicio"]
)

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def crear_orden(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        nueva_orden = service_order_repository.create(db, order_data)
        return nueva_orden
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo registrar la orden de servicio: {str(e)}"
        )