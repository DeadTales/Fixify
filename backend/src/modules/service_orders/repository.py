from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from src.modules.service_orders.models import ServiceOrderModel
from src.modules.service_orders.schema import OrderCreate
from src.modules.service_orders.models import StatusHistoryModel
# Importamos los modelos reales utilizando sus nombres correctos
from src.modules.clients.model import Client
from src.modules.equipment.model import Equipment
from src.modules.users.model import User  # <-- Importamos el modelo de usuario para validar al técnico

# Definición estricta del ciclo de vida y orden permitido de avance
VALID_TRANSITIONS = {
    "Recibido": ["En revisión"],
    "En revisión": ["Reparando"],
    "Reparando": ["Listo"],
    "Listo": ["Entregado"],
    "Entregado": []  # Estado final, no puede avanzar más
}

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

    def get_by_technician(self, db: Session, id_tecnico: int):
        """Devuelve todas las órdenes de servicio asignadas a un técnico específico."""
        return db.query(ServiceOrderModel).filter(ServiceOrderModel.id_tecnico == id_tecnico).all()

    def update_order_status(self, db: Session, id_orden: int, nuevo_estado: str) -> ServiceOrderModel:
        """Avanza el estado de la orden validando las reglas del ciclo de vida."""
        db_order = db.query(ServiceOrderModel).filter(ServiceOrderModel.id_orden == id_orden).first()
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La orden de servicio especificada no existe."
            )
        
        estado_actual = db_order.estado

        # Validar si la transición está permitida
        estados_permitidos = VALID_TRANSITIONS.get(estado_actual, [])
        if nuevo_estado not in estados_permitidos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transición no permitida. No se puede pasar de '{estado_actual}' a '{nuevo_estado}'. El flujo correcto es: Recibido -> En revisión -> Reparando -> Listo -> Entregado."
            )

        # Actualizar estado
        db_order.estado = nuevo_estado

        # Si se marca como Entregado, registramos automáticamente la fecha de entrega
        if nuevo_estado == "Entregado":
            db_order.fecha_entrega = func.now()

        db.commit()
        db.refresh(db_order)
        
        return db_order
    def update_order_status(self, db: Session, id_orden: int, nuevo_estado: str, id_usuario: int) -> ServiceOrderModel:
        """Avanza el estado de la orden, valida el ciclo de vida y registra el historial de cambios."""
        db_order = db.query(ServiceOrderModel).filter(ServiceOrderModel.id_orden == id_orden).first()
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La orden de servicio especificada no existe."
            )
        
        estado_actual = db_order.estado

        # Validar si la transición está permitida
        estados_permitidos = VALID_TRANSITIONS.get(estado_actual, [])
        if nuevo_estado not in estados_permitidos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transición no permitida. No se puede pasar de '{estado_actual}' a '{nuevo_estado}'. El flujo correcto es: Recibido -> En revisión -> Reparando -> Listo -> Entregado."
            )

        # Validar que el usuario responsable exista
        tecnico = db.query(User).filter(User.id_usuario == id_usuario).first()
        if not tecnico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El usuario con ID {id_usuario} no existe."
            )

        # Registrar la modificación en el historial de estados
        historial = StatusHistoryModel(
            id_orden=id_orden,
            id_usuario=id_usuario,
            estado_anterior=estado_actual,
            estado_nuevo=nuevo_estado
        )
        db.add(historial)

        # Actualizar estado de la orden
        db_order.estado = nuevo_estado

        # Si se marca como Entregado, registramos automáticamente la fecha de entrega
        if nuevo_estado == "Entregado":
            db_order.fecha_entrega = func.now()

        db.commit()
        db.refresh(db_order)
        
        return db_order
    def get_order_detail(self, db: Session, id_orden: int):
        """Devuelve el detalle de la orden de servicio junto con su historial de estados."""
        db_order = db.query(ServiceOrderModel).filter(ServiceOrderModel.id_orden == id_orden).first()
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La orden de servicio especificada no existe."
            )
        
        # Consultar el historial de estados de esta orden para la trazabilidad
        historial = db.query(StatusHistoryModel).filter(StatusHistoryModel.id_orden == id_orden).all()
        
        return {
            "orden": db_order,
            "historial": historial
        }
service_order_repository = ServiceOrderRepository()