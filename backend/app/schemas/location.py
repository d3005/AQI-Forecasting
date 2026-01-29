"""
Pydantic schemas for Location data validation
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LocationBase(BaseModel):
    """Base location schema with common fields"""
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    country: Optional[str] = Field(None, max_length=100, description="Country name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class LocationCreate(LocationBase):
    """Schema for creating a new location"""
    pass


class LocationResponse(LocationBase):
    """Schema for location response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LocationListResponse(BaseModel):
    """Schema for list of locations"""
    locations: list[LocationResponse]
    total: int
