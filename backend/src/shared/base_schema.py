from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """
    Esquema base para Pydantic. 
    Configurado para permitir la lectura de modelos de SQLAlchemy automáticamente.
    """
    model_config = ConfigDict(from_attributes=True)