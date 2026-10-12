from sqlalchemy.orm import Session
from src.modules.service_orders.models import ServiceOrderModel
from src.modules.service_orders.schema import OrderCreate

class ServiceOrderRepository:
    def create(self, db: Session, order: OrderCreate) -> ServiceOrderModel:
        db_order = ServiceOrderModel(
            id_cliente=order.id_cliente,
            id_equipo=order.id_equipo,
            id_tecnico=order.id_tecnico,
            estado=order.estado if order.estado else "Recibido"
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        db_order.folio = f"FIX-{db_order.id_orden:03d}"
        db.commit()
        db.refresh(db_order)
        
        return db_order

service_order_repository = ServiceOrderRepository()