#!/usr/bin/env python
"""
CertiForge Application Launcher
Runs the FastAPI server with Uvicorn.
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print("  CertiForge - High-Performance Bulk Certificate Generator")
    print("=" * 65)
    print("  Server URL:        http://127.0.0.1:8000")
    print("  Web Dashboard:     http://127.0.0.1:8000/")
    print("  Interactive Docs:  http://127.0.0.1:8000/docs")
    print("  ReDoc:             http://127.0.0.1:8000/redoc")
    print("=" * 65)
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
