"""
Facebook Prophet Model for Financial Forecasting
================================================

Implementation of Prophet model for time series forecasting with support for
seasonality, holidays, and external regressors.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

from models.base_model import BaseModel
from utils.helpers import calculate_model_metrics

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available. Install with: pip install prophet")

class ProphetModel(BaseModel):
    """Facebook Prophet model for time series forecasting."""
    
    def __init__(self, **kwargs):
        """
        Initialize Prophet model with custom parameters.
        
        Args:
            **kwargs: Prophet model parameters
        """
        super().__init__("Prophet")
        
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet library not available")
        
        # Prophet model parameters
        self.prophet_params = {
            'daily_seasonality': kwargs.get('daily_seasonality', False),
            'weekly_seasonality': kwargs.get('weekly_seasonality', True),
            'yearly_seasonality': kwargs.get('yearly_seasonality', True),
            'seasonality_mode': kwargs.get('seasonality_mode', 'multiplicative'),
            'changepoint_prior_scale': kwargs.get('changepoint_prior_scale', 0.05),
            'seasonality_prior_scale': kwargs.get('seasonality_prior_scale', 10.0),
            'holidays_prior_scale': kwargs.get('holidays_prior_scale', 10.0),
            'uncertainty_samples': kwargs.get('uncertainty_samples', 1000)
        }
        
        self.model = None
        self.training_data = None
        self.last_date = None
    
    def fit(self, data: pd.DataFrame, target_column: str = 'close') -> None:
        """
        Train the Prophet model on historical data.
        
        Args:
            data: Historical price data with datetime index
            target_column: Name of the target column to predict
        """
        try:
            self.logger.info(f"Training Prophet model on {len(data)} samples")
            
            # Prepare data in Prophet format
            prophet_data = pd.DataFrame({
                'ds': data.index,
                'y': data[target_column]
            })
            
            # Remove any NaN values
            prophet_data = prophet_data.dropna()
            
            if len(prophet_data) < 10:
                raise ValueError("Insufficient data for training Prophet model")
            
            # Initialize Prophet model
            self.model = Prophet(**self.prophet_params)
            
            # Add additional regressors if available
            regressor_columns = ['volume', 'volatility_20', 'rsi', 'macd']
            for col in regressor_columns:
                if col in data.columns:
                    prophet_data[col] = data[col].fillna(method='ffill')
                    self.model.add_regressor(col)
                    self.feature_columns.append(col)
            
            # Add custom seasonalities
            self.model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            self.model.add_seasonality(name='quarterly', period=91.25, fourier_order=8)
            
            # Fit the model
            self.model.fit(prophet_data)
            
            # Store training information
            self.training_data = prophet_data
            self.last_date = data.index[-1]
            self.is_fitted = True
            
            # Calculate training metrics
            in_sample_forecast = self.model.predict(prophet_data)
            actual = prophet_data['y'].values
            predicted = in_sample_forecast['yhat'].values
            
            self.training_metrics = calculate_model_metrics(actual, predicted)
            
            self.logger.info(f"Prophet model trained successfully. R²: {self.training_metrics.get('r2', 0):.4f}")
            
        except Exception as e:
            self.logger.error(f"Error training Prophet model: {e}")
            raise
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Generate forecasts using the trained Prophet model.
        
        Args:
            periods: Number of periods to forecast
            confidence_interval: Confidence level for prediction intervals
            
        Returns:
            DataFrame with predictions and confidence bounds
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=periods)
            
            # Add regressor values for future periods (forward fill last known values)
            for col in self.feature_columns:
                if col in self.training_data.columns:
                    # Forward fill the last known values
                    last_value = self.training_data[col].iloc[-1]
                    future[col] = self.training_data[col].reindex(future.index).fillna(last_value)
            
            # Generate forecast
            forecast = self.model.predict(future)
            
            # Extract forecast for the prediction period only
            forecast_period = forecast.tail(periods).copy()
            
            # Calculate confidence intervals based on the specified level
            alpha = 1 - confidence_interval
            lower_col = f'yhat_lower'
            upper_col = f'yhat_upper'
            
            # Prepare result DataFrame
            result = pd.DataFrame({
                'timestamp': forecast_period['ds'],
                'predicted_price': forecast_period['yhat'],
                'lower_bound': forecast_period[lower_col],
                'upper_bound': forecast_period[upper_col],
                'model': 'Prophet'
            })
            
            result.set_index('timestamp', inplace=True)
            
            self.logger.info(f"Generated {periods} predictions with Prophet model")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating Prophet predictions: {e}")
            raise
    
    def validate(self, validation_data: pd.DataFrame, target_column: str = 'close') -> Dict[str, float]:
        """
        Validate the model on out-of-sample data.
        
        Args:
            validation_data: Validation dataset
            target_column: Target column name
            
        Returns:
            Dictionary of validation metrics
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before validation")
        
        try:
            # Prepare validation data
            val_prophet_data = pd.DataFrame({
                'ds': validation_data.index,
                'y': validation_data[target_column]
            })
            
            # Add regressors if they exist
            for col in self.feature_columns:
                if col in validation_data.columns:
                    val_prophet_data[col] = validation_data[col]
            
            # Generate predictions for validation period
            predictions = self.model.predict(val_prophet_data)
            
            # Calculate metrics
            actual = val_prophet_data['y'].values
            predicted = predictions['yhat'].values
            
            metrics = calculate_model_metrics(actual, predicted)
            
            self.logger.info(f"Validation completed. MAE: {metrics.get('mae', 0):.4f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error during Prophet validation: {e}")
            return {}
    
    def get_components(self) -> Optional[pd.DataFrame]:
        """Get the forecast components (trend, seasonality, etc.)."""
        if not self.is_fitted:
            return None
        
        try:
            # Generate forecast for training period to get components
            forecast = self.model.predict(self.training_data)
            
            components = pd.DataFrame({
                'timestamp': forecast['ds'],
                'trend': forecast['trend'],
                'weekly': forecast.get('weekly', 0),
                'yearly': forecast.get('yearly', 0),
                'monthly': forecast.get('monthly', 0),
                'quarterly': forecast.get('quarterly', 0)
            })
            
            components.set_index('timestamp', inplace=True)
            return components
            
        except Exception as e:
            self.logger.error(f"Error getting Prophet components: {e}")
            return None
    
    def detect_changepoints(self) -> Optional[pd.DataFrame]:
        """Detect significant changepoints in the time series."""
        if not self.is_fitted:
            return None
        
        try:
            changepoints = self.model.changepoints
            changepoint_data = pd.DataFrame({
                'changepoint_date': changepoints,
                'trend_change': True
            })
            
            return changepoint_data
            
        except Exception as e:
            self.logger.error(f"Error detecting changepoints: {e}")
            return None
