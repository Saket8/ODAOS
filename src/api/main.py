# ODAOS Web API

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from src.api.routes import chat, viz, sessions, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("[ODAOS] API starting...")
    yield
    # Shutdown
    print("[ODAOS] API shutting down...")


app = FastAPI(
    title="ODAOS API",
    description="Oracle Database AI Operations System - Premium Dashboard API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend - allow all origins in development for SSE to work
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(viz.router, prefix="/api/viz", tags=["Visualizations"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])


@app.get("/")
async def root():
    return {
        "name": "ODAOS API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
