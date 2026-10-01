from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.conexion import get_db
from src.modules.auth.dependencies import verificar_rol_recepcion_o_admin
from src.modules.equipment.schema import EquipmentCreate
from src.modules.equipment.repository import equipment_repository

router = APIRouter(
    prefix="/equipos",
    tags=["Gestión de Equipos"],
    dependencies=[Depends(verificar_rol_recepcion_o_admin)]
)

@router.post("/", status_code=201)
def registrar_equipo(equipo: EquipmentCreate, db: Session = Depends(get_db)):
    nuevo_equipo = equipment_repository.create(db, equipo)
    
    # Generamos un folio formateado para recepción (Ej. EQ-001, EQ-015)
    folio_visible = f"EQ-{nuevo_equipo.id:03d}"
    
    return {
        "mensaje": "¡Equipo registrado correctamente!",
        "folio": folio_visible,  # <-- Esto es lo que verá la recepcionista en grande
        "detalles": {
            "id_interno": nuevo_equipo.id,
            "tipo": nuevo_equipo.tipo,
            "marca": nuevo_equipo.marca,
            "modelo": nuevo_equipo.modelo,
            "cliente_id": nuevo_equipo.client_id
        }
    }