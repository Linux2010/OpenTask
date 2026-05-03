"""
Bot TodoList - FastAPI Application

A lightweight task distribution system for managing multiple OpenClaw bot containers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
from app.admin import router as admin_router

app.include_router(task.router, prefix=settings.API_PREFIX)
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to admin"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OpenTask</title>
        <meta http-equiv="refresh" content="0;url=/admin/">
    </head>
    <body>
        <p>Redirecting to <a href="/admin/">Admin UI</a>...</p>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}