from typing import Generic, Type, TypeVar, List, Optional
from sqlalchemy.orm import Session
from src.database.conexion import Base

# Definimos tipos genéricos para los modelos de SQLAlchemy y los esquemas de Pydantic
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        Repositorio base con operaciones CRUD reutilizables.
        :दारा model: El modelo de SQLAlchemy (la tabla de la BD)
        """
        self.model = model

    def get_by_id(self, db: Session, id: int) -> Optional[ModelType]:
        """Obtiene un registro por su ID (Deserialización desde BD)"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Obtiene una lista paginada de registros"""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """Crea un nuevo registro a partir de un esquema de Pydantic"""
        obj_in_data = obj_in.model_dump() # Convierte el esquema Pydantic a diccionario
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: int) -> ModelType:
        """Elimina un registro por su ID"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj