from fastapi import FastAPI, HTTPException
from app.routes import router
from dotenv import load_dotenv
import os
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

# Import db for health checks
from app.db import init_database
import logging

# Configure logging
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)

app = FastAPI(title="SQL + Forecast API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = init_database()
    if not db_healthy:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return {
        "status": "healthy", 
        "service": "SQL + Forecast API", 
        "database": "connected"
    }

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check paths and file structure"""
    db_path = os.getenv('DB_PATH', 'data/northwind.db')
    abs_db_path = db_path if db_path.startswith('/app/') else os.path.abspath(db_path)
    
    return {
        "current_directory": os.getcwd(),
        "base_directory": str(BASE_DIR),
        "files_in_root": os.listdir('/app') if os.path.exists('/app') else [],
        "files_in_current": os.listdir('.'),
        "data_dir_exists": os.path.exists('data'),
        "data_dir_contents": os.listdir('data') if os.path.exists('data') else [],
        "db_path": db_path,
        "abs_db_path": abs_db_path,
        "db_file_exists": os.path.exists(abs_db_path),
        "env_file_exists": os.path.exists(dotenv_path)
    }

@app.get("/")
async def root():
    return {
        "message": "SQL + Forecast API is running", 
        "version": "1.0",
        "docs": "/docs"
    }

# Include your existing router
app.include_router(router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Application starting up...")
    # Test database connection
    if init_database():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed!")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )