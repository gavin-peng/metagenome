"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.db.database import init_db
from app.api.routes import router
from app.errors.handlers import (
    api_error_handler,
    value_error_handler,
    general_exception_handler
)
from app.errors.exceptions import APIError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RESTful API for managing genomic file assets (VCF, BAM, CRAM)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(router, tags=["files"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    logging.info("Database initialized")


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "healthy"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
