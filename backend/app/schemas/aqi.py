"""
Pydantic schemas for AQI data validation
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AQIReadingBase(BaseModel):
    """Base AQI reading schema"""
    pm25: Optional[float] = Field(None, ge=0, description="PM2.5 concentration (μg/m³)")
    pm10: Optional[float] = Field(None, ge=0, description="PM10 concentration (μg/m³)")
    o3: Optional[float] = Field(None, ge=0, description="Ozone concentration (μg/m³)")
    no2: Optional[float] = Field(None, ge=0, description="NO2 concentration (μg/m³)")
    so2: Optional[float] = Field(None, ge=0, description="SO2 concentration (μg/m³)")
    co: Optional[float] = Field(None, ge=0, description="CO concentration (μg/m³)")
    aqi_value: int = Field(..., ge=0, le=500, description="AQI value (0-500)")
    aqi_category: Optional[str] = Field(None, description="AQI category label")


class AQIReadingCreate(AQIReadingBase):
    """Schema for creating an AQI reading"""
    location_id: int
    recorded_at: datetime


class AQIReadingResponse(AQIReadingBase):
    """Schema for AQI reading response"""
    id: int
    location_id: int
    recorded_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class AQICurrentResponse(BaseModel):
    """Schema for current AQI response with location info"""
    location_id: int
    city: str
    country: Optional[str]
    aqi_value: int
    aqi_category: str
    pm25: Optional[float]
    pm10: Optional[float]
    o3: Optional[float]
    no2: Optional[float]
    so2: Optional[float]
    co: Optional[float]
    recorded_at: datetime
    health_advisory: str
    
    @staticmethod
    def get_health_advisory(aqi_value: int) -> str:
        """Get health advisory based on AQI value"""
        if aqi_value <= 50:
            return "Air quality is satisfactory, and air pollution poses little or no risk."
        elif aqi_value <= 100:
            return "Air quality is acceptable. However, there may be a risk for some people."
        elif aqi_value <= 150:
            return "Members of sensitive groups may experience health effects."
        elif aqi_value <= 200:
            return "Everyone may begin to experience health effects."
        elif aqi_value <= 300:
            return "Health warnings of emergency conditions. Everyone is more likely to be affected."
        else:
            return "Health alert: everyone may experience more serious health effects."


class AQIHistoryResponse(BaseModel):
    """Schema for historical AQI data"""
    readings: list[AQIReadingResponse]
    total: int
    location_id: int
    city: str
