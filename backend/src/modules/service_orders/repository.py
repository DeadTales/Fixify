from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.modules.service_orders.models import ServiceOrderModel
from src.modules.service_orders.schema import OrderCreate

# Importamos los modelos reales utilizando sus nombres correctos
from src.modules.clients.model import Client
from src.modules.equipment.model import Equipment
from src.modules.users.model import User  # <-- Importamos el modelo de usuario para validar al técnico

class ServiceOrderRepository:
    def create(self, db: Session, order: OrderCreate) -> ServiceOrderModel:
        
        # 1. Validar que el cliente exista
        cliente = db.query(Client).filter(Client.id == order.id_cliente).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El cliente con ID {order.id_cliente} no existe en el sistema."
            )
        
        # 2. Validar que el equipo exista
        equipo = db.query(Equipment).filter(Equipment.id == order.id_equipo).first()
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El equipo con ID {order.id_equipo} no existe en el sistema."
            )
        
        # 3. Validar compatibilidad (que el equipo pertenezca al cliente indicado)
        if equipo.client_id != order.id_cliente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El equipo especificado no pertenece al cliente seleccionado."
            )

        # 4. Validar técnico al crear (si se proporciona un id_tecnico desde el inicio)
        if order.id_tecnico:
            tecnico = db.query(User).filter(User.id_usuario == order.id_tecnico).first()
            if not tecnico:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El técnico con ID {order.id_tecnico} no existe."
                )
            if not tecnico.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede asignar la orden a un técnico inactivo o no disponible."
                )

        # 5. Si todo es correcto, registramos la orden
        db_order = ServiceOrderModel(
            id_cliente=order.id_cliente,
            id_equipo=order.id_equipo,
            id_tecnico=order.id_tecnico,
            estado=order.estado if order.estado else "Recibido"
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        # Generar el folio automático
        db_order.folio = f"FIX-{db_order.id_orden:03d}"
        db.commit()
        db.refresh(db_order)
        
        return db_order

    def assign_technician(self, db: Session, id_orden: int, id_tecnico: int) -> ServiceOrderModel:
        # 1. Verificar que la orden exista
        db_order = db.query(ServiceOrderModel).filter(ServiceOrderModel.id_orden == id_orden).first()
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La orden de servicio especificada no existe."
            )
        
        # 2. Verificar que el técnico exista
        tecnico = db.query(User).filter(User.id_usuario == id_tecnico).first()
        if not tecnico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El técnico con ID {id_tecnico} no existe."
            )
        
        # 3. Validar que el técnico esté activo
        if not tecnico.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede asignar o reasignar la orden a un técnico inactivo o no disponible."
            )
        
        # 4. Asignar y persistir el cambio de técnico
        db_order.id_tecnico = id_tecnico
        db.commit()
        db.refresh(db_order)
        
        return db_order

service_order_repository = ServiceOrderRepository()