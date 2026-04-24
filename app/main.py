"""
Bot TodoList - FastAPI Application

A lightweight task distribution system for managing multiple OpenClaw bot containers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="OpenTask API",
    description="Open-source task distribution system for OpenClaw bot containers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.routers import task

app.include_router(task.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OpenTask",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}