from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.modules.clients.model import Client
from src.modules.clients.schema import ClientCreate

class ClientRepository:
    def create(self, db: Session, client_in: ClientCreate):
        if client_in.direccion:
            raise HTTPException(status_code=422, detail='El SQL base no incluye direcci?n del cliente.')
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
            correo=client_in.correo
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

client_repository = ClientRepository()