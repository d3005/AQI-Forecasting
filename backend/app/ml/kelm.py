"""
Kernel Extreme Learning Machine (KELM) Implementation

KELM combines the advantages of ELM with kernel learning:
- No need to specify hidden layer neurons
- Uses kernel functions to map input to high-dimensional space
- Closed-form solution via regularized least squares

Reference:
Huang, G.B. et al. (2012). Extreme learning machine for regression and 
multiclass classification. IEEE Transactions on Systems, Man, and 
Cybernetics, Part B (Cybernetics), 42(2), 513-529.
"""

import numpy as np
from scipy import linalg
from typing import Optional, Literal


class KELM:
    """
    Kernel Extreme Learning Machine for regression.
    
    Uses RBF (Radial Basis Function) kernel by default.
    Hyperparameters C and gamma are optimized by Genetic Algorithm.
    
    Attributes:
        C: Regularization parameter (higher = less regularization)
        gamma: RBF kernel coefficient (higher = more localized)
        kernel: Kernel type ('rbf', 'linear', 'poly')
    """
    
    def __init__(
        self,
        C: float = 1.0,
        gamma: float = 0.1,
        kernel: Literal['rbf', 'linear', 'poly'] = 'rbf',
        degree: int = 3,  # For polynomial kernel
    ):
        """
        Initialize KELM.
        
        Args:
            C: Regularization parameter (0.01 to 1000)
            gamma: RBF kernel coefficient (0.001 to 10)
            kernel: Kernel type ('rbf', 'linear', 'poly')
            degree: Degree for polynomial kernel
        """
        self.C = C
        self.gamma = gamma
        self.kernel = kernel
        self.degree = degree
        
        # Training data (stored for prediction)
        self.X_train: Optional[np.ndarray] = None
        self.output_weights: Optional[np.ndarray] = None
        self._is_fitted = False
    
    def _compute_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """
        Compute kernel matrix K(X1, X2).
        
        For RBF: K(x, y) = exp(-gamma * ||x - y||^2)
        
        Args:
            X1: First set of samples (n1, features)
            X2: Second set of samples (n2, features)
            
        Returns:
            Kernel matrix of shape (n1, n2)
        """
        if self.kernel == 'rbf':
            # Efficient RBF kernel computation
            # ||x - y||^2 = ||x||^2 + ||y||^2 - 2 * x.y
            X1_sq = np.sum(X1 ** 2, axis=1).reshape(-1, 1)
            X2_sq = np.sum(X2 ** 2, axis=1).reshape(1, -1)
            sq_dist = X1_sq + X2_sq - 2 * np.dot(X1, X2.T)
            sq_dist = np.maximum(sq_dist, 0)  # Numerical stability
            return np.exp(-self.gamma * sq_dist)
            
        elif self.kernel == 'linear':
            return np.dot(X1, X2.T)
            
        elif self.kernel == 'poly':
            return (self.gamma * np.dot(X1, X2.T) + 1) ** self.degree
            
        else:
            raise ValueError(f"Unknown kernel: {self.kernel}")
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'KELM':
        """
        Train KELM model.
        
        Solves: beta = (K + I/C)^(-1) * y
        
        Where:
            K: Kernel matrix
            I: Identity matrix
            C: Regularization parameter
            
        Args:
            X: Training features (n_samples, n_features)
            y: Target values (n_samples,) or (n_samples, n_outputs)
            
        Returns:
            self (fitted model)
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        
        # Store training data for prediction
        self.X_train = X
        n_samples = X.shape[0]
        
        # Reshape y if needed
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        
        # Compute kernel matrix
        K = self._compute_kernel(X, X)
        
        # Add regularization: (K + I/C)
        regularization = np.eye(n_samples) / self.C
        K_reg = K + regularization
        
        # Solve for output weights using Cholesky decomposition
        # More numerically stable than direct inversion
        try:
            L = linalg.cholesky(K_reg, lower=True)
            self.output_weights = linalg.cho_solve((L, True), y)
        except linalg.LinAlgError:
            # Fallback to pseudo-inverse if Cholesky fails
            self.output_weights = linalg.lstsq(K_reg, y, lapack_driver='gelsy')[0]
        
        self._is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions for new samples.
        
        Args:
            X: Input features (n_samples, n_features)
            
        Returns:
            Predicted values (n_samples,)
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
            
        X = np.asarray(X, dtype=np.float64)
        
        # Compute kernel between new samples and training samples
        K_test = self._compute_kernel(X, self.X_train)
        
        # Predict: y_pred = K_test * beta
        predictions = np.dot(K_test, self.output_weights)
        
        return predictions.ravel()
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Compute R² score for predictions.
        
        Args:
            X: Input features
            y: True values
            
        Returns:
            R² score (1.0 = perfect fit)
        """
        y = np.asarray(y)
        y_pred = self.predict(X)
        
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        
        if ss_tot == 0:
            return 0.0
            
        return 1 - (ss_res / ss_tot)
    
    def get_params(self) -> dict:
        """Get model parameters"""
        return {
            'C': self.C,
            'gamma': self.gamma,
            'kernel': self.kernel,
            'degree': self.degree,
        }
    
    def set_params(self, **params) -> 'KELM':
        """Set model parameters"""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Square Error"""
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Error"""
    return np.mean(np.abs(y_true - y_pred))


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error"""
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
