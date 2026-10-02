from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.modules.equipment.model import Equipment
from src.modules.equipment.schema import EquipmentCreate
from src.modules.clients.model import Client

class EquipmentRepository:
    def get_all(self, db: Session):
        """db: sesión actual; devuelve los equipos ordenados por identificador."""
        return db.query(Equipment).order_by(Equipment.id).all()

    def create(self, db: Session, eq_in: EquipmentCreate):
        """db: sesión actual; eq_in: datos validados del equipo y su propietario."""
        # 1. Validar que el cliente dueno realmente exista
        # Solo necesitamos el ID; no consultamos otros datos del cliente.
        client = db.query(Client.id).filter(Client.id == eq_in.client_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El cliente especificado no existe en la base de datos."
            )
        
        # 2. Registrar el equipo
        db_equipment = Equipment(
            tipo=eq_in.tipo,
            marca=eq_in.marca,
            modelo=eq_in.modelo,
            numero_serie=eq_in.numero_serie,
            problema_reportado=eq_in.problema_reportado,
            client_id=eq_in.client_id
        )
        db.add(db_equipment)
        db.commit()
        db.refresh(db_equipment)
        return db_equipment

equipment_repository = EquipmentRepository()
