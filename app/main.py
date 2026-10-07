import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and storage directories exist
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield
    # Shutdown logic if any


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="High-performance, fault-isolated Bulk Certificate Generator API with PDF/PNG rendering, tracking, and retrieval.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for open frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routes
app.include_router(api_router)


# Frontend Web Dashboard Route
@app.get("/", response_class=HTMLResponse, tags=["Frontend Web UI"])
async def serve_dashboard():
    template_path = Path(__file__).resolve().parent / "templates" / "index.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"), status_code=200)


@app.get("/jobs/{job_id}", response_class=HTMLResponse, tags=["Frontend Web UI"])
async def serve_job_page(job_id: str):
    """Deep-link to the job monitor page."""
    template_path = Path(__file__).resolve().parent / "templates" / "index.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"), status_code=200)


@app.get("/verify/{certificate_code}", response_class=HTMLResponse, tags=["Frontend Web UI"])
async def serve_verify_page(certificate_code: str):
    """Deep-link to certificate verification page."""
    template_path = Path(__file__).resolve().parent / "templates" / "index.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"), status_code=200)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "storage_dir": str(settings.STORAGE_DIR),
        "database": "sqlite_wal"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
