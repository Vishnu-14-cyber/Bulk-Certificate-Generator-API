import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    APP_NAME: str = "Bulk Certificate Generator API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'certificates.db'}")
    
    # File Storage
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage" / "certificates")))
    
    # Server / Verification URL host
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Worker Settings
    MAX_WORKER_THREADS: int = int(os.getenv("MAX_WORKER_THREADS", "4"))
    
    class Config:
        arbitrary_types_allowed = True

settings = Settings()

# Ensure storage directory exists
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
