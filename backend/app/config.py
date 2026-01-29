"""
Configuration settings for the AQI Prediction System
Uses Pydantic Settings for environment variable management
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Real-Time AQI Prediction System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/aqi_db"
    
    # External APIs
    OPENWEATHERMAP_API_KEY: str = ""
    AQICN_API_TOKEN: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Scheduler
    DATA_FETCH_INTERVAL_MINUTES: int = 15
    MODEL_RETRAIN_INTERVAL_HOURS: int = 24
    
    # Default location (for demo)
    DEFAULT_LATITUDE: float = 28.6139  # Delhi
    DEFAULT_LONGITUDE: float = 77.2090
    DEFAULT_CITY: str = "Delhi"
    DEFAULT_COUNTRY: str = "India"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
