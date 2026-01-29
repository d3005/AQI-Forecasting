"""Database models package"""

from app.models.location import Location
from app.models.aqi_reading import AQIReading
from app.models.prediction import Prediction
from app.models.model_metadata import ModelMetadata

__all__ = ["Location", "AQIReading", "Prediction", "ModelMetadata"]
