"""
Main FastAPI application for the replenishment service.
Handles application startup, shutdown, and middleware configuration.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.config import settings
from app.database.connection import db_manager
from app.api.routes import router


# Configure logging
def setup_logging():
    """Setup application logging configuration."""
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file logger
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Replenishment Service...")
    
    try:
        # Setup logging
        setup_logging()
        
        # Connect to database
        await db_manager.connect()
        logger.info("Database connected successfully")
        
        # Load ML model
        if ml_service.is_model_loaded():
            logger.info("ML model loaded successfully")
        else:
            logger.warning("No ML model found - predictions will fail until model is trained")
        
        logger.info("Replenishment Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Replenishment Service...")
    
    try:
        await db_manager.disconnect()
        logger.info("Database disconnected successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("Replenishment Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Replenishment Service",
    description="AI-powered replenishment forecasting service using XGBoost",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include API routes
app.include_router(router, prefix="/api/v1", tags=["replenishment"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Replenishment Service",
        "version": "1.0.0",
        "description": "AI-powered replenishment forecasting using XGBoost",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Import ML service after app creation to avoid circular imports
from app.services.ml_service import ml_service 