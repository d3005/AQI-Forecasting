"""
Pydantic schemas for Prediction data validation
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PredictionBase(BaseModel):
    """Base prediction schema"""
    predicted_aqi: float = Field(..., ge=0, le=500, description="Predicted AQI value")
    predicted_category: Optional[str] = Field(None, description="Predicted AQI category")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Prediction confidence")


class PredictionCreate(PredictionBase):
    """Schema for creating a prediction"""
    location_id: int
    prediction_for: datetime


class PredictionResponse(PredictionBase):
    """Schema for prediction response"""
    id: int
    location_id: int
    prediction_for: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionListResponse(BaseModel):
    """Schema for list of predictions"""
    predictions: list[PredictionResponse]
    total: int
    location_id: int
    city: str
    
    
class PredictionWithActual(BaseModel):
    """Schema for prediction with actual comparison"""
    prediction: PredictionResponse
    actual_aqi: Optional[int] = None
    error: Optional[float] = None  # Absolute error if actual is available


class ModelInfoResponse(BaseModel):
    """Schema for model information"""
    model_version: str
    best_c: float
    best_gamma: float
    train_rmse: float
    val_rmse: float
    trained_at: datetime
    generations_run: Optional[int]
    population_size: Optional[int]
    
    class Config:
        from_attributes = True
