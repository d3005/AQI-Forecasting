"""
Predictor Service - High-level interface for AQI predictions

Manages:
- Model training and persistence
- Prediction generation
- Feature engineering from AQI readings
"""

import numpy as np
import joblib
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging
import io

from app.ml.ga_kelm import GAKELM, create_time_features, create_lag_features
from app.models import AQIReading, Prediction, ModelMetadata, Location
from app.config import settings

logger = logging.getLogger(__name__)


class PredictorService:
    """
    High-level service for AQI predictions using GA-KELM.
    
    Handles:
    - Training models from database readings
    - Generating predictions for future timestamps
    - Model versioning and persistence
    """
    
    # Feature configuration
    LAG_HOURS = [1, 2, 3, 6, 12, 24]  # Lag features to use
    
    def __init__(self):
        self.model: Optional[GAKELM] = None
        self.model_version: str = "1.0.0"
        self._is_loaded = False
    
    def _prepare_features(
        self, 
        readings: List[AQIReading]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features from AQI readings.
        
        Features include:
        - Lagged AQI values
        - Time-based features (hour, day of week, etc.)
        - Pollution component values
        
        Args:
            readings: List of AQI readings sorted by time
            
        Returns:
            Tuple of (X_features, y_targets)
        """
        # Extract values and timestamps
        aqi_values = np.array([r.aqi_value for r in readings])
        timestamps = [r.recorded_at for r in readings]
        
        # Create lag features
        lag_features, valid_indices = create_lag_features(aqi_values, self.LAG_HOURS)
        
        # Create time features for valid indices
        valid_timestamps = [timestamps[i] for i in valid_indices]
        time_features = create_time_features(valid_timestamps)
        
        # Get pollution components for valid indices
        pollution_features = []
        for i in valid_indices:
            r = readings[i]
            pollution_features.append([
                r.pm25 or 0,
                r.pm10 or 0,
                r.o3 or 0,
                r.no2 or 0,
            ])
        pollution_features = np.array(pollution_features)
        
        # Combine all features
        X = np.hstack([lag_features, time_features, pollution_features])
        
        # Target: next hour's AQI (shifted by 1)
        y = aqi_values[valid_indices]
        
        return X, y
    
    async def train_model(
        self, 
        readings: List[AQIReading],
        session: AsyncSession,
        population_size: int = 30,
        generations: int = 50,
    ) -> Optional[GAKELM]:
        """
        Train GA-KELM model from AQI readings.
        
        Args:
            readings: List of AQI readings
            session: Database session for saving model
            population_size: GA population size
            generations: GA generations
            
        Returns:
            Trained model or None if training fails
        """
        if len(readings) < 100:
            logger.warning("Not enough data for training (need at least 100 samples)")
            return None
        
        try:
            # Sort readings by time
            readings = sorted(readings, key=lambda r: r.recorded_at)
            
            # Prepare features
            X, y = self._prepare_features(readings)
            
            if len(X) < 50:
                logger.warning("Not enough valid samples after feature engineering")
                return None
            
            logger.info(f"Training with {len(X)} samples, {X.shape[1]} features")
            
            # Train model
            self.model = GAKELM(
                population_size=population_size,
                generations=generations,
                random_state=42
            )
            self.model.fit(X, y, verbose=True)
            
            # Update version
            self.model_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._is_loaded = True
            
            # Save to database
            await self._save_model_to_db(session)
            
            return self.model
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return None
    
    async def _save_model_to_db(self, session: AsyncSession):
        """Save trained model to database"""
        if not self.model:
            return
        
        # Serialize model to bytes
        buffer = io.BytesIO()
        joblib.dump(self.model, buffer)
        model_bytes = buffer.getvalue()
        
        metrics = self.model.get_metrics()
        
        model_meta = ModelMetadata(
            model_version=self.model_version,
            best_c=metrics['best_C'],
            best_gamma=metrics['best_gamma'],
            train_rmse=metrics['train_rmse'],
            val_rmse=metrics['val_rmse'],
            train_mae=metrics['train_mae'],
            val_mae=metrics['val_mae'],
            generations_run=metrics['generations_run'],
            population_size=metrics['population_size'],
            model_binary=model_bytes,
        )
        
        session.add(model_meta)
        await session.commit()
        logger.info(f"Model saved to database: {self.model_version}")
    
    async def load_latest_model(self, session: AsyncSession) -> bool:
        """
        Load the latest trained model from database.
        
        Returns:
            True if model loaded successfully
        """
        try:
            result = await session.execute(
                select(ModelMetadata)
                .order_by(desc(ModelMetadata.trained_at))
                .limit(1)
            )
            model_meta = result.scalar_one_or_none()
            
            if not model_meta or not model_meta.model_binary:
                logger.info("No trained model found in database")
                return False
            
            # Deserialize model
            buffer = io.BytesIO(model_meta.model_binary)
            self.model = joblib.load(buffer)
            self.model_version = model_meta.model_version
            self._is_loaded = True
            
            logger.info(f"Loaded model {self.model_version} from database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    async def predict_future(
        self,
        location_id: int,
        hours_ahead: int,
        session: AsyncSession
    ) -> List[Prediction]:
        """
        Generate predictions for future hours.
        
        Args:
            location_id: Location to predict for
            hours_ahead: Number of hours to predict
            session: Database session
            
        Returns:
            List of Prediction objects
        """
        # Load model if not loaded
        if not self._is_loaded:
            await self.load_latest_model(session)
        
        if not self.model:
            logger.warning("No model available for predictions")
            return []
        
        try:
            # Get recent readings for the location
            max_lag = max(self.LAG_HOURS)
            result = await session.execute(
                select(AQIReading)
                .where(AQIReading.location_id == location_id)
                .order_by(desc(AQIReading.recorded_at))
                .limit(max_lag + 1)
            )
            recent_readings = list(result.scalars().all())
            
            if len(recent_readings) < max_lag:
                logger.warning("Not enough recent readings for prediction")
                return []
            
            # Sort chronologically
            recent_readings = sorted(recent_readings, key=lambda r: r.recorded_at)
            
            predictions = []
            current_values = [r.aqi_value for r in recent_readings]
            last_reading = recent_readings[-1]
            base_time = last_reading.recorded_at
            
            for hour in range(1, hours_ahead + 1):
                prediction_time = base_time + timedelta(hours=hour)
                
                # Create features
                lag_features = [current_values[-(lag)] for lag in self.LAG_HOURS if lag <= len(current_values)]
                
                # Pad if needed
                while len(lag_features) < len(self.LAG_HOURS):
                    lag_features.append(lag_features[-1] if lag_features else 50)
                
                time_features = create_time_features([prediction_time])[0]
                
                # Use last known pollution values
                pollution_features = [
                    last_reading.pm25 or 0,
                    last_reading.pm10 or 0,
                    last_reading.o3 or 0,
                    last_reading.no2 or 0,
                ]
                
                # Combine features
                X = np.array([lag_features + list(time_features) + pollution_features])
                
                # Predict
                pred_value, confidence = self.model.predict_with_confidence(X)
                pred_aqi = float(np.clip(pred_value[0], 0, 500))
                
                # Create prediction object
                prediction = Prediction(
                    location_id=location_id,
                    predicted_aqi=pred_aqi,
                    predicted_category=Prediction.get_category(pred_aqi),
                    confidence=float(confidence[0]),
                    prediction_for=prediction_time,
                )
                predictions.append(prediction)
                
                # Update values for next prediction
                current_values.append(pred_aqi)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return []
    
    async def predict_single(
        self,
        features: np.ndarray
    ) -> Tuple[float, float]:
        """
        Make single prediction from feature array.
        
        Returns:
            Tuple of (predicted_aqi, confidence)
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        pred, conf = self.model.predict_with_confidence(features)
        return float(pred[0]), float(conf[0])


# Singleton instance
predictor_service = PredictorService()
