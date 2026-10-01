from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from src.database.conexion import get_db
from src.modules.auth.dependencies import verificar_rol_recepcion_o_admin
from src.modules.clients.schema import ClientCreate, ClientResponse
from src.modules.clients.repository import client_repository
from src.modules.clients.schema import ClientCreate, ClientResponse, ClientMessageResponse
from typing import List

router = APIRouter(
    prefix="/clientes",
    tags=["Gestión de Clientes"],
    dependencies=[Depends(verificar_rol_recepcion_o_admin)] # Solo Recepción o Admin pueden entrar aquí
)

@router.get("/buscar", response_model=List[ClientResponse])
def buscar_cliente_para_equipo(q: str, db: Session = Depends(get_db)):
    """
    Busca y confirma la existencia del cliente por nombre o teléfono 
    antes de proceder al registro de su equipo.
    """
    resultados = client_repository.buscar_cliente_por_termino(db, q)
    return resultados


@router.post("/", status_code=201) # 201 Created es el estándar HTTP para registros exitosos
def registrar_cliente(cliente: ClientCreate, db: Session = Depends(get_db)):
    # El repositorio ya valida si existe y lanza el error 400 si está duplicado
    nuevo_cliente = client_repository.create(db, cliente)
    
    return {
        "mensaje": "¡Cliente registrado correctamente en el sistema!",
        "cliente": nuevo_cliente
    }

@router.get("/", response_model=List[ClientResponse])
def listar_clientes(db: Session = Depends(get_db)):
    return client_repository.get_all(db)