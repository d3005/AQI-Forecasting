"""
Real-Time Air Quality Prediction System - Main Application

FastAPI backend with:
- REST API for AQI data and predictions
- WebSocket for real-time updates
- GA-KELM machine learning engine
- Background scheduler for data collection
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.config import settings
from app.database import init_db, close_db
from app.services.scheduler import scheduler_service
from app.routers import (
    aqi_router,
    predictions_router,
    locations_router,
    websocket_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Start background scheduler
        scheduler_service.start()
        logger.info("Background scheduler started")
        
        # Trigger initial data collection
        await scheduler_service.trigger_data_collection()
        logger.info("Initial data collection triggered")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    try:
        # Stop scheduler
        scheduler_service.stop()
        logger.info("Scheduler stopped")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Real-Time Air Quality Prediction System
    
    This API provides:
    
    ### 🌍 AQI Data
    - Current air quality readings from multiple locations
    - Historical AQI data and trends
    - Real-time updates via WebSocket
    
    ### 🤖 GA-KELM Predictions
    - Machine learning predictions using Genetic Algorithm optimized Kernel ELM
    - Hourly predictions up to 72 hours ahead
    - Prediction accuracy metrics
    
    ### 📍 Location Management
    - Add/remove monitoring locations
    - Global coverage via OpenWeatherMap API
    
    ### 🔌 Real-Time Updates
    - WebSocket connections for live updates
    - Automatic data refresh every 15 minutes
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(aqi_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")
app.include_router(websocket_router)


# Health check endpoints
@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws/aqi/{location_id}"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "scheduler_running": scheduler_service._is_running
    }


@app.get("/api/v1/status", tags=["health"])
async def api_status():
    """Detailed API status"""
    from app.database import async_session_maker
    from sqlalchemy import select, func
    from app.models import Location, AQIReading, Prediction, ModelMetadata
    
    async with async_session_maker() as session:
        # Get counts
        locations_count = await session.execute(select(func.count(Location.id)))
        readings_count = await session.execute(select(func.count(AQIReading.id)))
        predictions_count = await session.execute(select(func.count(Prediction.id)))
        models_count = await session.execute(select(func.count(ModelMetadata.id)))
        
        return {
            "status": "operational",
            "version": settings.APP_VERSION,
            "database": {
                "connected": True,
                "locations": locations_count.scalar(),
                "readings": readings_count.scalar(),
                "predictions": predictions_count.scalar(),
                "trained_models": models_count.scalar()
            },
            "scheduler": {
                "running": scheduler_service._is_running,
                "data_fetch_interval_minutes": settings.DATA_FETCH_INTERVAL_MINUTES,
                "model_retrain_interval_hours": settings.MODEL_RETRAIN_INTERVAL_HOURS
            },
            "api_endpoints": {
                "aqi": "/api/v1/aqi",
                "predictions": "/api/v1/predictions",
                "locations": "/api/v1/locations",
                "websocket": "/ws/aqi/{location_id}"
            }
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
