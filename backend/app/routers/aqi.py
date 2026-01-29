"""
AQI API Router
Endpoints for retrieving AQI data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models import Location, AQIReading
from app.schemas import (
    AQIReadingResponse, 
    AQICurrentResponse, 
    AQIHistoryResponse
)
from app.services.aqi_fetcher import aqi_fetcher

router = APIRouter(prefix="/aqi", tags=["aqi"])


@router.get("/current/{location_id}", response_model=AQICurrentResponse)
async def get_current_aqi(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current AQI for a specific location.
    
    Returns the most recent AQI reading along with health advisory.
    """
    # Get location
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found"
        )
    
    # Get most recent reading
    result = await db.execute(
        select(AQIReading)
        .where(AQIReading.location_id == location_id)
        .order_by(desc(AQIReading.recorded_at))
        .limit(1)
    )
    reading = result.scalar_one_or_none()
    
    if not reading:
        # Try to fetch fresh data
        aqi_data = await aqi_fetcher.fetch_current_aqi(
            location.latitude, 
            location.longitude
        )
        
        if aqi_data:
            reading = AQIReading(
                location_id=location_id,
                **{k: v for k, v in aqi_data.items() if k != 'source'}
            )
            db.add(reading)
            await db.commit()
            await db.refresh(reading)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No AQI data available for this location"
            )
    
    return AQICurrentResponse(
        location_id=location.id,
        city=location.city,
        country=location.country,
        aqi_value=reading.aqi_value,
        aqi_category=reading.aqi_category or AQIReading.get_category(reading.aqi_value),
        pm25=reading.pm25,
        pm10=reading.pm10,
        o3=reading.o3,
        no2=reading.no2,
        so2=reading.so2,
        co=reading.co,
        recorded_at=reading.recorded_at,
        health_advisory=AQICurrentResponse.get_health_advisory(reading.aqi_value)
    )


@router.get("/history/{location_id}", response_model=AQIHistoryResponse)
async def get_aqi_history(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical AQI data for a location.
    
    - **location_id**: Location ID
    - **hours**: Number of hours of history (1-720, default 24)
    """
    # Get location
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found"
        )
    
    # Get readings from last N hours
    cutoff = datetime.now() - timedelta(hours=hours)
    
    result = await db.execute(
        select(AQIReading)
        .where(
            AQIReading.location_id == location_id,
            AQIReading.recorded_at >= cutoff
        )
        .order_by(desc(AQIReading.recorded_at))
    )
    readings = result.scalars().all()
    
    return AQIHistoryResponse(
        readings=[AQIReadingResponse.model_validate(r) for r in readings],
        total=len(readings),
        location_id=location.id,
        city=location.city
    )


@router.get("/fetch/{location_id}", response_model=AQICurrentResponse)
async def fetch_fresh_aqi(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch fresh AQI data from external API and store it.
    
    Use this to manually trigger a data refresh.
    """
    # Get location
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found"
        )
    
    # Fetch from API
    aqi_data = await aqi_fetcher.fetch_current_aqi(
        location.latitude,
        location.longitude
    )
    
    if not aqi_data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to fetch AQI data from external API"
        )
    
    # Store reading
    reading = AQIReading(
        location_id=location_id,
        pm25=aqi_data.get("pm25"),
        pm10=aqi_data.get("pm10"),
        o3=aqi_data.get("o3"),
        no2=aqi_data.get("no2"),
        so2=aqi_data.get("so2"),
        co=aqi_data.get("co"),
        aqi_value=aqi_data.get("aqi_value", 0),
        aqi_category=aqi_data.get("aqi_category"),
        recorded_at=aqi_data.get("recorded_at", datetime.now()),
    )
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    
    return AQICurrentResponse(
        location_id=location.id,
        city=location.city,
        country=location.country,
        aqi_value=reading.aqi_value,
        aqi_category=reading.aqi_category or AQIReading.get_category(reading.aqi_value),
        pm25=reading.pm25,
        pm10=reading.pm10,
        o3=reading.o3,
        no2=reading.no2,
        so2=reading.so2,
        co=reading.co,
        recorded_at=reading.recorded_at,
        health_advisory=AQICurrentResponse.get_health_advisory(reading.aqi_value)
    )


@router.get("/stats/{location_id}")
async def get_aqi_stats(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=720),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AQI statistics for a location.
    
    Returns min, max, average, and trend data.
    """
    # Get location
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found"
        )
    
    # Get readings
    cutoff = datetime.now() - timedelta(hours=hours)
    result = await db.execute(
        select(AQIReading)
        .where(
            AQIReading.location_id == location_id,
            AQIReading.recorded_at >= cutoff
        )
        .order_by(AQIReading.recorded_at)
    )
    readings = result.scalars().all()
    
    if not readings:
        return {
            "location_id": location_id,
            "city": location.city,
            "hours": hours,
            "count": 0,
            "min": None,
            "max": None,
            "avg": None,
            "trend": "unknown"
        }
    
    aqi_values = [r.aqi_value for r in readings]
    
    # Calculate trend (comparing first and second halves)
    mid = len(aqi_values) // 2
    if mid > 0:
        first_half_avg = sum(aqi_values[:mid]) / mid
        second_half_avg = sum(aqi_values[mid:]) / (len(aqi_values) - mid)
        
        if second_half_avg > first_half_avg * 1.1:
            trend = "worsening"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "improving"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    return {
        "location_id": location_id,
        "city": location.city,
        "hours": hours,
        "count": len(readings),
        "min": min(aqi_values),
        "max": max(aqi_values),
        "avg": round(sum(aqi_values) / len(aqi_values), 1),
        "trend": trend
    }
