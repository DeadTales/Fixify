from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.config.settings import settings
from src.database.conexion import get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend para el sistema de gestión de taller de reparaciones",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None
)

@app.get("/")
def root():
    return {
        "status": "success", 
        "environment": settings.ENVIRONMENT,
        "message": "Bienvenido al backend de Fixify"
    }

# --- NUEVO ENDPOINT DE HEALTH CHECK ---
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)