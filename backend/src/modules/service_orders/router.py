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

@router.patch("/{id_orden}/estado", response_model=OrderResponse)
def cambiar_estado_orden(id_orden: int, nuevo_estado: str, id_usuario: int, db: Session = Depends(get_db)):
    """Actualiza el estado de la orden de servicio y guarda la traza en el historial."""
    try:
        return service_order_repository.update_order_status(db, id_orden, nuevo_estado, id_usuario)
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo registrar el cambio de estado: {str(e)}"
        )
@router.get("/tecnico/{id_tecnico}", response_model=list[OrderResponse])
def listar_ordenes_por_tecnico(id_tecnico: int, db: Session = Depends(get_db)):
    """Obtiene el listado de órdenes asignadas a un técnico específico."""
    try:
        return service_order_repository.get_by_technician(db, id_tecnico)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudieron obtener las órdenes del técnico: {str(e)}"
        )
@router.get("/{id_orden}", response_model=dict)
def obtener_detalle_orden(id_orden: int, db: Session = Depends(get_db)):
    """Obtiene la información detallada de una orden de servicio y su historial de estados."""
    try:
        return service_order_repository.get_order_detail(db, id_orden)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo obtener el detalle de la orden: {str(e)}"
        )