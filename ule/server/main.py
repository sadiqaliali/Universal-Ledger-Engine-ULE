"""Unified ULE Server - Serving both REST API and Web UI."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="ULE Professional Server",
    version="1.1.0"
)

# Templates setup (use absolute path in production if needed)
templates = Jinja2Templates(
    directory="ule/server/templates"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Web Interface Route ---
@app.get("/", response_class=HTMLResponse)
async def serve_web_ui(request: Request):
    # Prevent frontend JS crashes
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "connected": True
        }
    )

# --- Health Check ---
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "ULE Server"
    }

if __name__ == "__main__":
    uvicorn.run(
        "ule.server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
