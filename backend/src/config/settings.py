from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Metadatos del proyecto
    PROJECT_NAME: str = "Fixify API"
    VERSION: str = "1.0.0"
    
    # Entorno actual (por defecto desarrollo, pero cambiará a 'production' en la nube)
    ENVIRONMENT: str = "development" 
    
    # Credenciales y conexiones
    DATABASE_URL: Optional[str] = None
    SECRET_KEY: str = "super_secreto_para_jwt_aqui" # Lo usaremos después para el login

    # Pydantic Settings busca automáticamente el archivo .env en la raíz
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instanciamos la clase para poder importarla en otros archivos
settings = Settings()