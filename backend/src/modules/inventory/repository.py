from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.modules.inventory.schema import MaterialCreate, MaterialUpdate
from src.modules.inventory.models import MaterialModel, ConsumoMaterialModel, StockAlertModel

class InventoryRepository:
    def evaluar_alerta_stock(self, existencia_actual: int, stock_minimo: int) -> bool:
        """
        Compara la existencia actual con el stock mínimo configurado.
        Retorna True si la existencia es menor o igual al mínimo, indicando que debe activarse la alerta.
        """
        return existencia_actual <= stock_minimo

    def create_material(self, db: Session, material: MaterialCreate) -> MaterialModel:
        try:
            db_material = MaterialModel(
                clave=material.clave,
                descripcion=material.descripcion,
                unidad=material.unidad,
                existencia_actual=material.existencia_actual,
                stock_minimo=material.stock_minimo
            )
            db.add(db_material)
            db.commit()
            db.refresh(db_material)
            return db_material
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al registrar el material en la base de datos: {str(e)}"
            )

    def update_material(self, db: Session, id_material: int, material_update: MaterialUpdate) -> MaterialModel:
        db_material = db.query(MaterialModel).filter(MaterialModel.id_material == id_material).first()
        if not db_material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El material con ID {id_material} no existe en el inventario."
            )
        
        try:
            update_data = material_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_material, key, value)
            
            db.commit()
            db.refresh(db_material)
            return db_material
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al actualizar el material: {str(e)}"
            )

    def get_materials(self, db: Session):
        return db.query(MaterialModel).all()
    
    def get_low_stock_materials(self, db: Session):
        """Obtiene los materiales cuya existencia actual es menor al stock mínimo."""
        all_materials = self.get_materials(db)
        return [m for m in all_materials if m.existencia_actual < m.stock_minimo]

    def registrar_consumo_material(self, db: Session, id_orden: int, id_material: int, cantidad: int, id_usuario: int = None) -> ConsumoMaterialModel:
        # 1. Validar existencia del material
        db_material = db.query(MaterialModel).filter(MaterialModel.id_material == id_material).first()
        if not db_material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El material con ID {id_material} no se encuentra registrado en el inventario."
            )
        
        # 2. Validar stock suficiente
        if db_material.existencia_actual < cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para '{db_material.descripcion}'. Existencia actual: {db_material.existencia_actual}, cantidad solicitada: {cantidad}."
            )
        
        try:
            # 3. Descontar stock y registrar bitácora de manera transaccional
            db_material.existencia_actual -= cantidad

            db_consumo = ConsumoMaterialModel(
                id_orden=id_orden,
                id_material=id_material,
                cantidad_utilizada=cantidad,
                id_usuario=id_usuario
            )
            db.add(db_consumo)
            db.commit()
            db.refresh(db_consumo)
            
            return db_consumo
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error crítico al actualizar el inventario y registrar el consumo: {str(e)}"
            )

    def get_consumos_by_orden(self, db: Session, id_orden: int):
        results = (
            db.query(
                ConsumoMaterialModel.id_consum,
                ConsumoMaterialModel.id_orden,
                ConsumoMaterialModel.id_material,
                ConsumoMaterialModel.cantidad_utilizada,
                ConsumoMaterialModel.id_usuario,
                MaterialModel.descripcion.label("material_descripcion"),
                MaterialModel.unidad
            )
            .join(MaterialModel, ConsumoMaterialModel.id_material == MaterialModel.id_material)
            .filter(ConsumoMaterialModel.id_orden == id_orden)
            .all()
        )
        return results
    
    def _verificar_y_registrar_alerta(self, db: Session, db_material: MaterialModel):
        """Registra una alerta en el historial si la existencia actual es menor o igual al stock mínimo."""
        if db_material.existencia_actual <= db_material.stock_minimo:
            db_alerta = StockAlertModel(
                id_material=db_material.id_material,
                existencia_actual=db_material.existencia_actual,
                stock_minimo=db_material.stock_minimo
            )
            db.add(db_alerta)

    def registrar_consumo_material(self, db: Session, id_orden: int, id_material: int, cantidad: int, id_usuario: int = None) -> ConsumoMaterialModel:
        db_material = db.query(MaterialModel).filter(MaterialModel.id_material == id_material).first()
        if not db_material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El material con ID {id_material} no se encuentra registrado en el inventario."
            )
        
        if db_material.existencia_actual < cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para '{db_material.descripcion}'. Existencia actual: {db_material.existencia_actual}, cantidad solicitada: {cantidad}."
            )
        
        try:
            # 1. Descontar stock
            db_material.existencia_actual -= cantidad

            # 2. Registrar el consumo en la bitácora
            db_consumo = ConsumoMaterialModel(
                id_orden=id_orden,
                id_material=id_material,
                cantidad_utilizada=cantidad,
                id_usuario=id_usuario
            )
            db.add(db_consumo)

            # 3. Evaluar y registrar la alerta si el stock es menor o igual al mínimo
            if db_material.existencia_actual <= db_material.stock_minimo:
                db_alerta = StockAlertModel(
                    id_material=db_material.id_material,
                    existencia_actual=db_material.existencia_actual,
                    stock_minimo=db_material.stock_minimo
                )
                db.add(db_alerta)

            db.commit()
            db.refresh(db_consumo)
            
            return db_consumo
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error crítico al actualizar el inventario y registrar el consumo: {str(e)}"
            )

    def get_alertas_stock(self, db: Session):
        """Obtiene el historial completo de alertas de inventario bajo."""
        results = (
            db.query(
                StockAlertModel.id_alerta,
                StockAlertModel.id_material,
                StockAlertModel.existencia_actual,
                StockAlertModel.stock_minimo,
                StockAlertModel.fecha_alerta,
                MaterialModel.descripcion.label("material_descripcion")
            )
            .join(MaterialModel, StockAlertModel.id_material == MaterialModel.id_material)
            .order_by(StockAlertModel.fecha_alerta.desc())
            .all()
        )
        return results
inventory_repository = InventoryRepository()