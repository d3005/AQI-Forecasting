"""
Prediction model for storing GA-KELM AQI predictions
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Prediction(Base):
    """
    Represents a predicted AQI value from the GA-KELM model.
    Stores prediction details including confidence and target time.
    """
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    
    # Prediction values
    predicted_aqi = Column(Float, nullable=False)
    predicted_category = Column(String(50))
    confidence = Column(Float)  # Model confidence score (0-1)
    
    # Time for which prediction is made
    prediction_for = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # When prediction was generated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    location = relationship("Location", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, aqi={self.predicted_aqi}, for='{self.prediction_for}')>"
    
    @staticmethod
    def get_category(aqi_value: float) -> str:
        """Determine AQI category based on predicted value"""
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
