from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.config.settings import settings
from src.database.conexion import get_db, engine, Base 
from src.modules.auth.router import router as auth_router
# IMPORTANTE: Importa tu modelo de usuario aquí para que SQLAlchemy lo detecte y cree la tabla
from src.modules.users.model import User 
from src.modules.users.router import router as users_router
from src.modules.clients.router import router as clients_router
from src.modules.equipment.router import router as equipment_router



# --- CREACIÓN DE TABLAS EN SUPABASE ---
# Esta línea le dice a PostgreSQL que cree las tablas si no existen
Base.metadata.create_all(bind=engine)

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
    return {
        "status": "success", 
        "environment": settings.ENVIRONMENT,
        "message": "Bienvenido al backend de Fixify"
    }

@app.get("/health", tags=["Status"])
def health_check(db: Session = Depends(get_db)):
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