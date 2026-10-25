from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from src.database.conexion import get_db
from src.modules.inventory.schema import MaterialCreate, MaterialUpdate, MaterialResponse
from src.modules.inventory.repository import inventory_repository
from src.modules.inventory.schema import MaterialCreate, MaterialUpdate, MaterialResponse, ConsumoCreate
from src.modules.inventory.schema import ConsumoCreate, ConsumoResponse
from src.modules.inventory.schema import StockAlertResponse

router = APIRouter(prefix="/inventario", tags=["Inventario"])

@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def crear_material(material: MaterialCreate, db: Session = Depends(get_db)):
    return inventory_repository.create_material(db, material)

@router.patch("/{id_material}", response_model=MaterialResponse)
def modificar_material(id_material: int, material_update: MaterialUpdate, db: Session = Depends(get_db)):
    return inventory_repository.update_material(db, id_material, material_update)

@router.get("/", response_model=list[MaterialResponse])
def listar_materiales(db: Session = Depends(get_db)):
    return inventory_repository.get_materials(db)

@router.post("/consumos", status_code=status.HTTP_201_CREATED, response_model=ConsumoResponse)
def registrar_consumo_material(consumo: ConsumoCreate, db: Session = Depends(get_db)):
    """Registra el consumo de una refacción, validando stock y generando bitácora."""
    return inventory_repository.registrar_consumo_material(
        db=db,
        id_orden=consumo.id_orden,
        id_material=consumo.id_material,
        cantidad=consumo.cantidad_utilizada,
        id_usuario=consumo.id_usuario
    )
@router.get("/bajo-stock", response_model=list[MaterialResponse])
def listar_materiales_bajo_stock(db: Session = Depends(get_db)):
    """Obtiene únicamente las refacciones cuya existencia está por debajo del mínimo."""
    try:
        return inventory_repository.get_low_stock_materials(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudieron obtener los materiales con bajo stock: {str(e)}"
        )
@router.post("/consumos", status_code=status.HTTP_201_CREATED)
def registrar_consumo_material(consumo: ConsumoCreate, db: Session = Depends(get_db)):
    """Registra el consumo de una refacción, descuenta el stock y guarda la bitácora."""
    try:
        return inventory_repository.registrar_consumo_material(
            db=db,
            id_orden=consumo.id_orden,
            id_material=consumo.id_material,
            cantidad=consumo.cantidad_utilizada,
            id_usuario=consumo.id_usuario
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo registrar el consumo del material: {str(e)}"
        )
@router.get("/consumos/orden/{id_orden}", response_model=list[ConsumoResponse])
def listar_consumos_por_orden(id_orden: int, db: Session = Depends(get_db)):
    return inventory_repository.get_consumos_by_orden(db, id_orden)

@router.get("/alertas", response_model=list[StockAlertResponse])
def listar_alertas_stock(db: Session = Depends(get_db)):
    """Obtiene el historial de alertas y eventos generados por inventario bajo."""
    try:
        return inventory_repository.get_alertas_stock(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo obtener el historial de alertas: {str(e)}"
        )