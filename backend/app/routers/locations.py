"""
Locations API Router
Endpoints for managing monitored locations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Location
from app.schemas import LocationCreate, LocationResponse, LocationListResponse

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=LocationListResponse)
async def list_locations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all monitored locations.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    result = await db.execute(
        select(Location)
        .order_by(Location.city)
        .offset(skip)
        .limit(limit)
    )
    locations = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(select(Location))
    total = len(count_result.scalars().all())
    
    return LocationListResponse(
        locations=[LocationResponse.model_validate(loc) for loc in locations],
        total=total
    )


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific location by ID.
    """
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found"
        )
    
    return LocationResponse.model_validate(location)


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new location to monitor.
    
    - **city**: City name
    - **country**: Country name (optional)
    - **latitude**: Latitude coordinate (-90 to 90)
    - **longitude**: Longitude coordinate (-180 to 180)
    """
    # Check for duplicate
    result = await db.execute(
        select(Location).where(
            Location.latitude == location_data.latitude,
            Location.longitude == location_data.longitude
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location with these coordinates already exists"
        )
    
    location = Location(**location_data.model_dump())
    db.add(location)
    await db.commit()
    await db.refresh(location)
    
    return LocationResponse.model_validate(location)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a location and all its associated data.
    """
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found"
        )
    
    await db.delete(location)
    await db.commit()
