from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database.domain_models import ServiceOrder
from src.modules.equipment.model import Equipment
from fastapi import HTTPException, status
from src.modules.clients.model import Client
from src.modules.clients.schema import ClientCreate

class ClientRepository:
    def create(self, db: Session, client_in: ClientCreate):
        # 1. Validar si ya existe un cliente con el mismo teléfono
        cliente_existente = db.query(Client).filter(Client.telefono == client_in.telefono).first()

        if cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El cliente con el número de teléfono {client_in.telefono} ya se encuentra registrado."
            )

        # 2. Si no existe, procedemos a crearlo normalmente
        db_client = Client(
            nombre=client_in.nombre,
            telefono=client_in.telefono,
            correo=client_in.correo,
        )
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client

    def get_all(self, db: Session):
        return db.query(Client).all()
    def buscar_cliente_por_termino(self, db: Session, termino: str):
        # Permite buscar coincidencias parciales por teléfono o nombre
        return db.query(Client).filter(
            (Client.telefono.ilike(f"%{termino}%")) |
            (Client.nombre.ilike(f"%{termino}%"))
        ).all()


    def update(self, db: Session, record_id: int, values: ClientCreate):
        record = db.get(Client, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro no encontrado.')
        if db.query(Client.id).filter(Client.telefono == values.telefono, Client.id != record_id).first():
            raise HTTPException(status_code=409, detail='El teléfono ya pertenece a otro cliente.')
        for name, value in values.model_dump().items():
            setattr(record, name, value)
        self._commit(db)
        db.refresh(record)
        return record

    def delete(self, db: Session, record_id: int):
        record = db.get(Client, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro no encontrado.')
        if db.query(Equipment.id).filter(Equipment.client_id == record_id).first():
            raise HTTPException(status_code=409, detail='El cliente tiene equipos asociados. No puede eliminarse.')
        if db.query(ServiceOrder.id_orden).filter(ServiceOrder.id_cliente == record_id).first():
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

client_repository = ClientRepository()
