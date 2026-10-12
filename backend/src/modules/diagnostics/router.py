from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.database.conexion import get_db
from src.modules.diagnostics.schema import DiagnosticCreate, DiagnosticResponse
from src.modules.diagnostics.repository import diagnostic_repository

router = APIRouter(
    prefix="/diagnosticos",
    tags=["Gestión de Diagnósticos"]
)

@router.post("", response_model=DiagnosticResponse, status_code=status.HTTP_200_OK)
@router.post("/", response_model=DiagnosticResponse, status_code=status.HTTP_200_OK)
def guardar_o_actualizar_diagnostico(data: DiagnosticCreate, db: Session = Depends(get_db)):
    """Registra un nuevo diagnóstico o actualiza el existente si la orden está en estado abierto."""
    return diagnostic_repository.create_or_update_diagnostic(db, data)