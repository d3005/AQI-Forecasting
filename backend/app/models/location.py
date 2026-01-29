"""
Location model for monitoring locations
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class Location(Base):
    """
    Represents a geographic location being monitored for AQI.
    Each location can have multiple AQI readings and predictions.
    """
    
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    aqi_readings = relationship("AQIReading", back_populates="location", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="location", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Location(id={self.id}, city='{self.city}', country='{self.country}')>"
