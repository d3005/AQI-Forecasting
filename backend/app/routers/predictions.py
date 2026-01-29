"""
Predictions API Router
Endpoints for GA-KELM AQI predictions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models import Location, AQIReading, Prediction, ModelMetadata
from app.schemas import (
    PredictionResponse,
    PredictionListResponse,
    ModelInfoResponse
)
from app.ml.predictor import predictor_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{location_id}", response_model=PredictionListResponse)
async def get_predictions(
    location_id: int,
    hours_ahead: int = Query(default=24, ge=1, le=72, description="Hours ahead to show"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AQI predictions for a location.
    
    - **location_id**: Location ID
    - **hours_ahead**: Number of hours to predict (1-72, default 24)
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
    
    # Get existing predictions for the future
    now = datetime.now()
    result = await db.execute(
        select(Prediction)
        .where(
            Prediction.location_id == location_id,
            Prediction.prediction_for >= now,
            Prediction.prediction_for <= now + timedelta(hours=hours_ahead)
        )
        .order_by(Prediction.prediction_for)
    )
    predictions = result.scalars().all()
    
    # If no predictions, generate them
    if not predictions:
        predictions = await predictor_service.predict_future(
            location_id=location_id,
            hours_ahead=hours_ahead,
            session=db
        )
        
        if predictions:
            for pred in predictions:
                db.add(pred)
            await db.commit()
            
            # Refresh to get IDs
            result = await db.execute(
                select(Prediction)
                .where(
                    Prediction.location_id == location_id,
                    Prediction.prediction_for >= now
                )
                .order_by(Prediction.prediction_for)
                .limit(hours_ahead)
            )
            predictions = result.scalars().all()
    
    return PredictionListResponse(
        predictions=[PredictionResponse.model_validate(p) for p in predictions],
        total=len(predictions),
        location_id=location.id,
        city=location.city
    )


@router.post("/generate/{location_id}")
async def generate_predictions(
    location_id: int,
    hours_ahead: int = Query(default=24, ge=1, le=72),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate fresh predictions for a location.
    
    This will overwrite any existing future predictions.
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
    
    # Delete existing future predictions
    now = datetime.now()
    result = await db.execute(
        select(Prediction)
        .where(
            Prediction.location_id == location_id,
            Prediction.prediction_for >= now
        )
    )
    old_predictions = result.scalars().all()
    for pred in old_predictions:
        await db.delete(pred)
    
    # Generate new predictions
    predictions = await predictor_service.predict_future(
        location_id=location_id,
        hours_ahead=hours_ahead,
        session=db
    )
    
    if not predictions:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate predictions. Model may not be trained yet."
        )
    
    for pred in predictions:
        db.add(pred)
    await db.commit()
    
    return {
        "message": f"Generated {len(predictions)} predictions for {location.city}",
        "location_id": location_id,
        "hours_ahead": hours_ahead,
        "predictions_count": len(predictions)
    }


@router.post("/train")
async def trigger_training(
    population_size: int = Query(default=30, ge=10, le=100),
    generations: int = Query(default=50, ge=10, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger model training using all available data.
    
    - **population_size**: GA population size (10-100)
    - **generations**: GA generations (10-200)
    
    Note: Training may take several minutes depending on data size.
    """
    # Get training data from last 30 days
    cutoff = datetime.now() - timedelta(days=30)
    result = await db.execute(
        select(AQIReading)
        .where(AQIReading.recorded_at >= cutoff)
        .order_by(AQIReading.recorded_at)
    )
    readings = list(result.scalars().all())
    
    if len(readings) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient data for training. Have {len(readings)}, need at least 100 readings."
        )
    
    # Train model
    model = await predictor_service.train_model(
        readings=readings,
        session=db,
        population_size=population_size,
        generations=generations
    )
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model training failed. Check logs for details."
        )
    
    metrics = model.get_metrics()
    
    return {
        "message": "Model training completed successfully",
        "model_version": predictor_service.model_version,
        "train_rmse": metrics['train_rmse'],
        "val_rmse": metrics['val_rmse'],
        "best_C": metrics['best_C'],
        "best_gamma": metrics['best_gamma'],
        "generations_run": metrics['generations_run']
    }


@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info(
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about the current trained model.
    """
    result = await db.execute(
        select(ModelMetadata)
        .order_by(desc(ModelMetadata.trained_at))
        .limit(1)
    )
    model_meta = result.scalar_one_or_none()
    
    if not model_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trained model found. Trigger training first."
        )
    
    return ModelInfoResponse.model_validate(model_meta)


@router.get("/accuracy/{location_id}")
async def get_prediction_accuracy(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Get prediction accuracy by comparing past predictions with actual values.
    
    Returns MAE and RMSE for predictions made in the last N hours.
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
    
    now = datetime.now()
    cutoff = now - timedelta(hours=hours)
    
    # Get past predictions
    result = await db.execute(
        select(Prediction)
        .where(
            Prediction.location_id == location_id,
            Prediction.prediction_for >= cutoff,
            Prediction.prediction_for < now
        )
        .order_by(Prediction.prediction_for)
    )
    predictions = result.scalars().all()
    
    if not predictions:
        return {
            "location_id": location_id,
            "city": location.city,
            "hours_evaluated": hours,
            "predictions_count": 0,
            "mae": None,
            "rmse": None,
            "message": "No predictions available for evaluation"
        }
    
    # Match predictions with actual readings
    errors = []
    for pred in predictions:
        # Find closest actual reading
        result = await db.execute(
            select(AQIReading)
            .where(
                AQIReading.location_id == location_id,
                AQIReading.recorded_at >= pred.prediction_for - timedelta(minutes=30),
                AQIReading.recorded_at <= pred.prediction_for + timedelta(minutes=30)
            )
            .order_by(AQIReading.recorded_at)
            .limit(1)
        )
        actual = result.scalar_one_or_none()
        
        if actual:
            errors.append(abs(pred.predicted_aqi - actual.aqi_value))
    
    if not errors:
        return {
            "location_id": location_id,
            "city": location.city,
            "hours_evaluated": hours,
            "predictions_count": len(predictions),
            "matched_count": 0,
            "mae": None,
            "rmse": None,
            "message": "No matching actual readings found"
        }
    
    mae = sum(errors) / len(errors)
    rmse = (sum(e**2 for e in errors) / len(errors)) ** 0.5
    
    return {
        "location_id": location_id,
        "city": location.city,
        "hours_evaluated": hours,
        "predictions_count": len(predictions),
        "matched_count": len(errors),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "accuracy_percentage": round(100 - (mae / 5), 1)  # Rough accuracy estimate
    }
