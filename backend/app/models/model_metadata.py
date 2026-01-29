"""
Model Metadata for storing trained GA-KELM model information
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, LargeBinary, func
from app.database import Base


class ModelMetadata(Base):
    """
    Stores metadata and binary data for trained GA-KELM models.
    Tracks hyperparameters found by genetic algorithm.
    """
    
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False, index=True)
    
    # Best hyperparameters from GA
    best_c = Column(Float)           # Regularization parameter
    best_gamma = Column(Float)       # RBF kernel coefficient
    
    # Performance metrics
    train_rmse = Column(Float)
    val_rmse = Column(Float)
    train_mae = Column(Float)
    val_mae = Column(Float)
    
    # GA optimization details
    generations_run = Column(Integer)
    population_size = Column(Integer)
    
    # Timestamps
    trained_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Serialized model binary
    model_binary = Column(LargeBinary)
    
    def __repr__(self):
        return f"<ModelMetadata(version='{self.model_version}', rmse={self.val_rmse})>"
