"""
Background Scheduler Service
Handles periodic data collection and model retraining
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import logging

from app.config import settings
from app.database import async_session_maker
from app.models import Location, AQIReading, Prediction
from app.services.aqi_fetcher import aqi_fetcher

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages background jobs for:
    1. Periodic AQI data collection from external APIs
    2. Model retraining schedule
    3. Prediction generation
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False
        
    def start(self):
        """Start the scheduler with configured jobs"""
        if self._is_running:
            return
            
        # Add data collection job
        self.scheduler.add_job(
            self._collect_aqi_data,
            trigger=IntervalTrigger(minutes=settings.DATA_FETCH_INTERVAL_MINUTES),
            id="collect_aqi_data",
            name="Collect AQI Data",
            replace_existing=True,
        )
        
        # Add model retraining job
        self.scheduler.add_job(
            self._retrain_model,
            trigger=IntervalTrigger(hours=settings.MODEL_RETRAIN_INTERVAL_HOURS),
            id="retrain_model",
            name="Retrain GA-KELM Model",
            replace_existing=True,
        )
        
        # Add prediction generation job (every hour)
        self.scheduler.add_job(
            self._generate_predictions,
            trigger=IntervalTrigger(hours=1),
            id="generate_predictions",
            name="Generate Predictions",
            replace_existing=True,
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info("Scheduler started successfully")
        
    def stop(self):
        """Stop the scheduler"""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler stopped")
    
    async def _collect_aqi_data(self):
        """
        Collect AQI data for all monitored locations.
        Runs every DATA_FETCH_INTERVAL_MINUTES.
        """
        logger.info("Starting AQI data collection...")
        
        async with async_session_maker() as session:
            try:
                # Get all monitored locations
                result = await session.execute(select(Location))
                locations = result.scalars().all()
                
                if not locations:
                    logger.info("No locations to monitor, creating default location")
                    # Create default location if none exist
                    default_location = Location(
                        city=settings.DEFAULT_CITY,
                        country=settings.DEFAULT_COUNTRY,
                        latitude=settings.DEFAULT_LATITUDE,
                        longitude=settings.DEFAULT_LONGITUDE,
                    )
                    session.add(default_location)
                    await session.commit()
                    locations = [default_location]
                
                # Fetch and store AQI data for each location
                for location in locations:
                    try:
                        aqi_data = await aqi_fetcher.fetch_current_aqi(
                            location.latitude, 
                            location.longitude
                        )
                        
                        if aqi_data:
                            reading = AQIReading(
                                location_id=location.id,
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
                            session.add(reading)
                            logger.info(f"Collected AQI data for {location.city}: AQI={reading.aqi_value}")
                        else:
                            logger.warning(f"No AQI data available for {location.city}")
                            
                    except Exception as e:
                        logger.error(f"Error collecting data for {location.city}: {e}")
                        continue
                
                await session.commit()
                logger.info("AQI data collection completed")
                
            except Exception as e:
                logger.error(f"Error in data collection job: {e}")
                await session.rollback()
    
    async def _retrain_model(self):
        """
        Retrain GA-KELM model with latest data.
        Runs every MODEL_RETRAIN_INTERVAL_HOURS.
        """
        logger.info("Starting model retraining...")
        
        try:
            # Import here to avoid circular imports
            from app.ml.predictor import predictor_service
            
            async with async_session_maker() as session:
                # Get training data from last 30 days
                cutoff_date = datetime.now() - timedelta(days=30)
                result = await session.execute(
                    select(AQIReading)
                    .where(AQIReading.recorded_at >= cutoff_date)
                    .order_by(AQIReading.recorded_at)
                )
                readings = result.scalars().all()
                
                if len(readings) < 100:
                    logger.warning("Not enough data for retraining (need at least 100 samples)")
                    return
                
                # Retrain model
                await predictor_service.train_model(readings, session)
                logger.info("Model retraining completed")
                
        except Exception as e:
            logger.error(f"Error in model retraining: {e}")
    
    async def _generate_predictions(self):
        """
        Generate predictions for all locations.
        Runs every hour.
        """
        logger.info("Starting prediction generation...")
        
        try:
            from app.ml.predictor import predictor_service
            
            async with async_session_maker() as session:
                # Get all locations
                result = await session.execute(select(Location))
                locations = result.scalars().all()
                
                for location in locations:
                    try:
                        # Generate predictions for next 24 hours
                        predictions = await predictor_service.predict_future(
                            location_id=location.id,
                            hours_ahead=24,
                            session=session
                        )
                        
                        if predictions:
                            for pred in predictions:
                                session.add(pred)
                            
                            logger.info(f"Generated {len(predictions)} predictions for {location.city}")
                            
                    except Exception as e:
                        logger.error(f"Error generating predictions for {location.city}: {e}")
                        continue
                
                await session.commit()
                logger.info("Prediction generation completed")
                
        except Exception as e:
            logger.error(f"Error in prediction generation: {e}")
    
    async def trigger_data_collection(self):
        """Manually trigger data collection"""
        await self._collect_aqi_data()
    
    async def trigger_prediction(self):
        """Manually trigger prediction generation"""
        await self._generate_predictions()


# Singleton instance
scheduler_service = SchedulerService()
