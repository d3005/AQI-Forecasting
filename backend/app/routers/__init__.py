"""API Routers Package"""

from app.routers.aqi import router as aqi_router
from app.routers.predictions import router as predictions_router
from app.routers.locations import router as locations_router
from app.routers.websocket import router as websocket_router

__all__ = ["aqi_router", "predictions_router", "locations_router", "websocket_router"]
