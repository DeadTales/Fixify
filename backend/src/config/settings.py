from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fixify API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development" 
    
    # Variables obligatorias
    DATABASE_URL: str 
    SECRET_KEY: str 

    # Aquí le decimos a Pydantic que el archivo se llama exactamente "DataBase.env"
    model_config = SettingsConfigDict(env_file="DataBase.env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()