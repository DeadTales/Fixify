from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database.domain_models import ServiceOrder
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

        if eq_in.numero_serie and db.query(Equipment.id).filter(
            Equipment.numero_serie == eq_in.numero_serie
        ).first():
            raise HTTPException(status_code=409, detail='Ya existe un equipo con este número de serie.')
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


    def update(self, db: Session, record_id: int, values: EquipmentCreate):
        record = db.get(Equipment, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro no encontrado.')
        if db.get(Client, values.client_id) is None:
            raise HTTPException(status_code=404, detail='El cliente especificado no existe.')
        if values.numero_serie and db.query(Equipment.id).filter(
            Equipment.numero_serie == values.numero_serie, Equipment.id != record_id
        ).first():
            raise HTTPException(status_code=409, detail='Ya existe otro equipo con este número de serie.')
        if record.client_id != values.client_id and db.query(ServiceOrder.id_orden).filter(
            ServiceOrder.id_equipo == record_id
        ).first():
            raise HTTPException(status_code=409, detail='No se puede cambiar el propietario de un equipo con órdenes.')
        for name, value in values.model_dump().items():
            setattr(record, name, value)
        self._commit(db)
        db.refresh(record)
        return record

    def delete(self, db: Session, record_id: int):
        record = db.get(Equipment, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro no encontrado.')
        if db.query(ServiceOrder.id_orden).filter(ServiceOrder.id_equipo == record_id).first():
            raise HTTPException(status_code=409, detail='El registro tiene órdenes asociadas. Se conserva su historial.')
        db.delete(record)
        self._commit(db)

    @staticmethod
    def _commit(db):
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail='La operación entra en conflicto con registros relacionados.')

equipment_repository = EquipmentRepository()
