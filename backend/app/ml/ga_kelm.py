"""
GA-KELM: Genetic Algorithm - Kernel Extreme Learning Machine

Combines KELM with GA for automatic hyperparameter optimization.
This is the main ML engine for AQI prediction.

Features:
- Automatic C and gamma optimization via GA
- Feature preprocessing and normalization
- Time-series feature engineering for AQI prediction
- Model persistence using joblib

Reference:
Wang, X. et al. (2018). GA-KELM: Genetic-Algorithm-Improved Kernel 
Extreme Learning Machine for Traffic Flow Forecasting. Electronics.
"""

import numpy as np
import joblib
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging

from app.ml.kelm import KELM, calculate_rmse, calculate_mae
from app.ml.genetic_algorithm import GeneticAlgorithm

logger = logging.getLogger(__name__)


class GAKELM:
    """
    GA-KELM: Combined Genetic Algorithm and Kernel ELM.
    
    Automatically optimizes KELM hyperparameters using GA,
    then trains the final model with optimal parameters.
    
    Attributes:
        population_size: GA population size
        generations: GA generations
        test_size: Validation split ratio
        random_state: Random seed
    """
    
    def __init__(
        self,
        population_size: int = 30,
        generations: int = 50,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.8,
        test_size: float = 0.2,
        random_state: Optional[int] = 42,
    ):
        """
        Initialize GA-KELM.
        
        Args:
            population_size: Number of individuals in GA
            generations: Maximum GA generations
            mutation_rate: GA mutation rate
            crossover_rate: GA crossover rate
            test_size: Fraction for validation
            random_state: Random seed
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.test_size = test_size
        self.random_state = random_state
        
        # Components
        self.ga: Optional[GeneticAlgorithm] = None
        self.kelm: Optional[KELM] = None
        self.scaler_X: Optional[StandardScaler] = None
        self.scaler_y: Optional[StandardScaler] = None
        
        # Best parameters found by GA
        self.best_C: Optional[float] = None
        self.best_gamma: Optional[float] = None
        
        # Training metrics
        self.train_rmse: Optional[float] = None
        self.val_rmse: Optional[float] = None
        self.train_mae: Optional[float] = None
        self.val_mae: Optional[float] = None
        
        # Metadata
        self.trained_at: Optional[datetime] = None
        self.model_version: str = "1.0.0"
        self._is_fitted = False
    
    def _preprocess_features(
        self, 
        X: np.ndarray, 
        fit: bool = False
    ) -> np.ndarray:
        """
        Preprocess features using StandardScaler.
        
        Args:
            X: Input features
            fit: Whether to fit the scaler
            
        Returns:
            Scaled features
        """
        if fit:
            self.scaler_X = StandardScaler()
            return self.scaler_X.fit_transform(X)
        else:
            return self.scaler_X.transform(X)
    
    def _preprocess_target(
        self, 
        y: np.ndarray, 
        fit: bool = False
    ) -> np.ndarray:
        """Preprocess target values"""
        y = y.reshape(-1, 1)
        if fit:
            self.scaler_y = StandardScaler()
            return self.scaler_y.fit_transform(y).ravel()
        else:
            return self.scaler_y.transform(y).ravel()
    
    def _inverse_transform_target(self, y: np.ndarray) -> np.ndarray:
        """Inverse transform target values"""
        return self.scaler_y.inverse_transform(y.reshape(-1, 1)).ravel()
    
    def fit(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        verbose: bool = True
    ) -> 'GAKELM':
        """
        Train GA-KELM model.
        
        1. Split data into train/validation
        2. Run GA to find optimal C and gamma
        3. Train final KELM with optimal parameters
        4. Calculate performance metrics
        
        Args:
            X: Training features (n_samples, n_features)
            y: Target values (n_samples,)
            verbose: Whether to log progress
            
        Returns:
            self (fitted model)
        """
        logger.info("Starting GA-KELM training...")
        
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        
        # Preprocess
        X_scaled = self._preprocess_features(X, fit=True)
        y_scaled = self._preprocess_target(y, fit=True)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y_scaled,
            test_size=self.test_size,
            random_state=self.random_state
        )
        
        logger.info(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
        
        # Define fitness function for GA
        def fitness_function(C: float, gamma: float) -> float:
            """Evaluate KELM with given hyperparameters"""
            kelm = KELM(C=C, gamma=gamma, kernel='rbf')
            kelm.fit(X_train, y_train)
            y_pred = kelm.predict(X_val)
            
            # Return negative MSE (GA maximizes fitness)
            mse = np.mean((y_val - y_pred) ** 2)
            return -mse
        
        # Run Genetic Algorithm
        self.ga = GeneticAlgorithm(
            population_size=self.population_size,
            generations=self.generations,
            mutation_rate=self.mutation_rate,
            crossover_rate=self.crossover_rate,
            random_state=self.random_state,
        )
        
        logger.info("Running Genetic Algorithm optimization...")
        self.best_C, self.best_gamma = self.ga.evolve(
            fitness_function, 
            verbose=verbose
        )
        
        logger.info(f"Optimal parameters found: C={self.best_C:.4f}, gamma={self.best_gamma:.6f}")
        
        # Train final model with optimal parameters on full training data
        self.kelm = KELM(C=self.best_C, gamma=self.best_gamma, kernel='rbf')
        self.kelm.fit(X_scaled, y_scaled)
        
        # Calculate metrics
        y_train_pred = self.kelm.predict(X_train)
        y_val_pred = self.kelm.predict(X_val)
        
        # Inverse transform for metrics in original scale
        y_train_orig = self._inverse_transform_target(y_train)
        y_train_pred_orig = self._inverse_transform_target(y_train_pred)
        y_val_orig = self._inverse_transform_target(y_val)
        y_val_pred_orig = self._inverse_transform_target(y_val_pred)
        
        self.train_rmse = calculate_rmse(y_train_orig, y_train_pred_orig)
        self.val_rmse = calculate_rmse(y_val_orig, y_val_pred_orig)
        self.train_mae = calculate_mae(y_train_orig, y_train_pred_orig)
        self.val_mae = calculate_mae(y_val_orig, y_val_pred_orig)
        
        self.trained_at = datetime.now()
        self._is_fitted = True
        
        logger.info(f"Training complete. Train RMSE: {self.train_rmse:.4f}, Val RMSE: {self.val_rmse:.4f}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Input features (n_samples, n_features)
            
        Returns:
            Predicted AQI values
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        
        X = np.asarray(X, dtype=np.float64)
        X_scaled = self._preprocess_features(X, fit=False)
        y_scaled = self.kelm.predict(X_scaled)
        
        # Inverse transform to original scale
        return self._inverse_transform_target(y_scaled)
    
    def predict_with_confidence(
        self, 
        X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions with confidence estimates.
        
        Uses prediction variance as confidence measure.
        
        Args:
            X: Input features
            
        Returns:
            Tuple of (predictions, confidence_scores)
        """
        predictions = self.predict(X)
        
        # Simple confidence based on distance to training data
        # Higher confidence when closer to training samples
        X_scaled = self._preprocess_features(X, fit=False)
        distances = []
        
        for x in X_scaled:
            dist = np.min(np.sum((self.kelm.X_train - x) ** 2, axis=1))
            distances.append(dist)
        
        distances = np.array(distances)
        
        # Convert distance to confidence (0-1)
        # Use exponential decay
        confidence = np.exp(-0.1 * distances)
        confidence = np.clip(confidence, 0.5, 1.0)  # Min 50% confidence
        
        return predictions, confidence
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get training metrics"""
        return {
            'train_rmse': self.train_rmse,
            'val_rmse': self.val_rmse,
            'train_mae': self.train_mae,
            'val_mae': self.val_mae,
            'best_C': self.best_C,
            'best_gamma': self.best_gamma,
            'trained_at': self.trained_at,
            'model_version': self.model_version,
            'generations_run': len(self.ga.fitness_history) if self.ga else 0,
            'population_size': self.population_size,
        }
    
    def save(self, filepath: str) -> None:
        """Save model to file"""
        model_data = {
            'kelm': self.kelm,
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'best_C': self.best_C,
            'best_gamma': self.best_gamma,
            'train_rmse': self.train_rmse,
            'val_rmse': self.val_rmse,
            'train_mae': self.train_mae,
            'val_mae': self.val_mae,
            'trained_at': self.trained_at,
            'model_version': self.model_version,
            'population_size': self.population_size,
            'generations': self.generations,
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'GAKELM':
        """Load model from file"""
        model_data = joblib.load(filepath)
        
        instance = cls()
        instance.kelm = model_data['kelm']
        instance.scaler_X = model_data['scaler_X']
        instance.scaler_y = model_data['scaler_y']
        instance.best_C = model_data['best_C']
        instance.best_gamma = model_data['best_gamma']
        instance.train_rmse = model_data['train_rmse']
        instance.val_rmse = model_data['val_rmse']
        instance.train_mae = model_data.get('train_mae')
        instance.val_mae = model_data.get('val_mae')
        instance.trained_at = model_data['trained_at']
        instance.model_version = model_data['model_version']
        instance.population_size = model_data.get('population_size', 30)
        instance.generations = model_data.get('generations', 50)
        instance._is_fitted = True
        
        logger.info(f"Model loaded from {filepath}")
        return instance


def create_time_features(timestamps: List[datetime]) -> np.ndarray:
    """
    Create time-based features for AQI prediction.
    
    Features:
    - Hour of day (sine/cosine encoded)
    - Day of week (sine/cosine encoded)
    - Month (sine/cosine encoded)
    - Is weekend
    - Is rush hour
    
    Args:
        timestamps: List of datetime objects
        
    Returns:
        Feature array (n_samples, n_time_features)
    """
    features = []
    
    for ts in timestamps:
        # Hour encoding (cyclical)
        hour_sin = np.sin(2 * np.pi * ts.hour / 24)
        hour_cos = np.cos(2 * np.pi * ts.hour / 24)
        
        # Day of week encoding (cyclical)
        dow_sin = np.sin(2 * np.pi * ts.weekday() / 7)
        dow_cos = np.cos(2 * np.pi * ts.weekday() / 7)
        
        # Month encoding (cyclical)
        month_sin = np.sin(2 * np.pi * ts.month / 12)
        month_cos = np.cos(2 * np.pi * ts.month / 12)
        
        # Binary features
        is_weekend = 1.0 if ts.weekday() >= 5 else 0.0
        is_rush_hour = 1.0 if ts.hour in [7, 8, 9, 17, 18, 19] else 0.0
        
        features.append([
            hour_sin, hour_cos,
            dow_sin, dow_cos,
            month_sin, month_cos,
            is_weekend, is_rush_hour
        ])
    
    return np.array(features)


def create_lag_features(
    values: np.ndarray, 
    lags: List[int] = [1, 2, 3, 6, 12, 24]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create lag features for time series prediction.
    
    Args:
        values: AQI values array
        lags: List of lag periods (in hours)
        
    Returns:
        Tuple of (features, valid_indices)
    """
    n = len(values)
    max_lag = max(lags)
    
    features = []
    for i in range(max_lag, n):
        lag_features = [values[i - lag] for lag in lags]
        features.append(lag_features)
    
    return np.array(features), np.arange(max_lag, n)
