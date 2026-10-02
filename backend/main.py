# Punto de entrada FastAPI: registra rutas y modelos sin modificar el esquema SQL.
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.config.settings import settings
from src.database.conexion import get_db, engine, Base 
from src.modules.auth.router import router as auth_router
# Registra el modelo de usuario en los metadatos compartidos.
from src.modules.users.model import User 
from src.modules.users.router import router as users_router
from src.modules.clients.router import router as clients_router
from src.modules.equipment.router import router as equipment_router



# Registra entidades de mantenimiento; no crea tablas ni migra al importar.
from src.database import domain_models

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend para el sistema de gestión de taller de reparaciones",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None
)

# --- REGISTRO DE RUTAS (ROUTERS) ---
# El router debe conectarse inmediatamente después de crear "app"
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(clients_router)
app.include_router(equipment_router)
# --- ENDPOINTS GLOBALES ---
@app.get("/")
def root():
    """Devuelve información general de la API, sin consultar la base de datos."""
    return {
        "status": "success", 
        "environment": settings.ENVIRONMENT,
        "message": "Bienvenido al backend de Fixify"
    }

@app.get("/health", tags=["Status"])
def health_check(db: Session = Depends(get_db)):
    """db: sesión inyectada; verifica conectividad con SELECT 1, no todo el esquema."""
    try:
        # Intentamos ejecutar la consulta más básica en SQL
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        # Si falla, devolvemos un error 503 (Servicio no disponible)
        raise HTTPException(
            status_code=503, 
            detail=f"Error conectando a la base de datos: {str(e)}"
        )
    
    return {
        "api_status": "running",
        "db_status": db_status,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION
    }

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
