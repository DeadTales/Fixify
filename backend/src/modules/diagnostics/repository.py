from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.modules.diagnostics.models import DiagnosticModel
from src.modules.diagnostics.schema import DiagnosticCreate
from src.modules.service_orders.models import ServiceOrderModel

class DiagnosticRepository:
    def create_or_update_diagnostic(self, db: Session, data: DiagnosticCreate) -> DiagnosticModel:
        # 1. Validar que la orden de servicio exista
        orden = db.query(ServiceOrderModel).filter(ServiceOrderModel.id_orden == data.id_orden).first()
        if not orden:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La orden de servicio especificada no existe."
            )
        
        # 2. Restricción por estado: Solo permitir registrar/modificar si está abierto
        estados_abiertos = ["Recibido", "En Diagnóstico"]
        if orden.estado not in estados_abiertos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede registrar o modificar el diagnóstico porque la orden se encuentra en estado '{orden.estado}'."
            )

        # 3. Buscar si ya existe un diagnóstico para esta orden
        diagnostico = db.query(DiagnosticModel).filter(DiagnosticModel.id_orden == data.id_orden).first()
        
        if diagnostico:
            # Modificación si ya existe
            diagnostico.descripcion = data.descripcion
        else:
            # Creación si no existe
            diagnostico = DiagnosticModel(
                id_orden=data.id_orden,
                descripcion=data.descripcion
            )
            db.add(diagnostico)
            
        db.commit()
        db.refresh(diagnostico)
        return diagnostico

diagnostic_repository = DiagnosticRepository()