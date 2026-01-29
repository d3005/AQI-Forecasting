"""
AQI Reading model for storing air quality measurements
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class AQIReading(Base):
    """
    Represents a single AQI reading from a monitoring location.
    Contains pollutant concentrations and calculated AQI value.
    """
    
    __tablename__ = "aqi_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    
    # Pollutant concentrations (μg/m³)
    pm25 = Column(Float)  # Fine particulate matter
    pm10 = Column(Float)  # Coarse particulate matter
    o3 = Column(Float)    # Ozone
    no2 = Column(Float)   # Nitrogen dioxide
    so2 = Column(Float)   # Sulfur dioxide
    co = Column(Float)    # Carbon monoxide
    
    # Calculated AQI
    aqi_value = Column(Integer, nullable=False, index=True)
    aqi_category = Column(String(50))  # Good, Moderate, Unhealthy, etc.
    
    # Timestamps
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    location = relationship("Location", back_populates="aqi_readings")
    
    def __repr__(self):
        return f"<AQIReading(id={self.id}, aqi={self.aqi_value}, recorded_at='{self.recorded_at}')>"
    
    @staticmethod
    def get_category(aqi_value: int) -> str:
        """Determine AQI category based on value"""
        if aqi_value <= 50:
            return "Good"
        elif aqi_value <= 100:
            return "Moderate"
        elif aqi_value <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi_value <= 200:
            return "Unhealthy"
        elif aqi_value <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
