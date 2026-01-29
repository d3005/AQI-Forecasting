"""Pydantic schemas package"""

from app.schemas.aqi import (
    AQIReadingCreate,
    AQIReadingResponse,
    AQICurrentResponse,
    AQIHistoryResponse,
)
from app.schemas.prediction import (
    PredictionCreate,
    PredictionResponse,
    PredictionListResponse,
)
from app.schemas.location import (
    LocationCreate,
    LocationResponse,
    LocationListResponse,
)

__all__ = [
    "AQIReadingCreate",
    "AQIReadingResponse", 
    "AQICurrentResponse",
    "AQIHistoryResponse",
    "PredictionCreate",
    "PredictionResponse",
    "PredictionListResponse",
    "LocationCreate",
    "LocationResponse",
    "LocationListResponse",
]
