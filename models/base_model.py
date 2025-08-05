"""
Base Model Interface for Financial Forecasting
==============================================

Abstract base class defining the interface for all forecasting models.
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import pickle
from pathlib import Path

class BaseModel(ABC):
    """Abstract base class for all forecasting models."""
    
    def __init__(self, model_name: str):
        """
        Initialize the base model.
        
        Args:
            model_name: Name identifier for the model
        """
        self.model_name = model_name
        self.logger = logging.getLogger(f"{__name__}.{model_name}")
        self.is_fitted = False
        self.feature_columns = []
        self.model = None
        self.training_metrics = {}
        
    @abstractmethod
    def fit(self, data: pd.DataFrame, target_column: str = 'close') -> None:
        """
        Train the model on historical data.
        
        Args:
            data: Historical price data with datetime index
            target_column: Name of the target column to predict
        """
        pass
    
    @abstractmethod
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Generate forecasts for the specified number of periods.
        
        Args:
            periods: Number of periods to forecast
            confidence_interval: Confidence level for prediction intervals
            
        Returns:
            DataFrame with predictions and confidence bounds
        """
        pass
    
    @abstractmethod
    def validate(self, validation_data: pd.DataFrame, target_column: str = 'close') -> Dict[str, float]:
        """
        Validate the model on out-of-sample data.
        
        Args:
            validation_data: Validation dataset
            target_column: Target column name
            
        Returns:
            Dictionary of validation metrics
        """
        pass
    
    def save_model(self, filepath: str) -> bool:
        """Save the trained model to disk."""
        try:
            model_data = {
                'model': self.model,
                'model_name': self.model_name,
                'is_fitted': self.is_fitted,
                'feature_columns': self.feature_columns,
                'training_metrics': self.training_metrics
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.logger.info(f"Model saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """Load a trained model from disk."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.model_name = model_data['model_name']
            self.is_fitted = model_data['is_fitted']
            self.feature_columns = model_data['feature_columns']
            self.training_metrics = model_data.get('training_metrics', {})
            
            self.logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance if available."""
        return None
    
    def get_model_info(self) -> Dict:
        """Get model information and metadata."""
        return {
            'model_name': self.model_name,
            'is_fitted': self.is_fitted,
            'feature_columns': self.feature_columns,
            'training_metrics': self.training_metrics
        }
