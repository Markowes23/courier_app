"""
Ensemble Model for Financial Forecasting
========================================

Combines multiple forecasting models (Prophet, LSTM) using weighted averaging
and advanced ensemble techniques for improved prediction accuracy.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.base_model import BaseModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
from utils.helpers import calculate_model_metrics

class EnsembleModel(BaseModel):
    """Ensemble model combining multiple forecasting approaches."""
    
    def __init__(self, models: Optional[List[BaseModel]] = None, **kwargs):
        """
        Initialize ensemble model with component models.
        
        Args:
            models: List of component models to ensemble
            **kwargs: Additional parameters for model weighting
        """
        super().__init__("Ensemble")
        
        # Initialize component models if not provided
        if models is None:
            self.component_models = []
            
            # Add Prophet model (if available)
            try:
                prophet_model = ProphetModel()
                self.component_models.append(prophet_model)
            except ImportError:
                self.logger.warning("Prophet model not available")
            
            # Add LSTM model (if available)
            try:
                lstm_model = LSTMModel(sequence_length=30)
                self.component_models.append(lstm_model)
            except ImportError:
                self.logger.warning("LSTM model not available")
        else:
            self.component_models = models
        
        if not self.component_models:
            raise ValueError("No component models available for ensemble")
        
        # Ensemble parameters
        self.weighting_method = kwargs.get('weighting_method', 'performance')  # 'equal', 'performance', 'adaptive'
        self.model_weights = kwargs.get('model_weights', None)
        self.validation_split = kwargs.get('validation_split', 0.2)
        
        # Performance tracking
        self.component_metrics = {}
        self.ensemble_history = []
        
    def fit(self, data: pd.DataFrame, target_column: str = 'close') -> None:
        """
        Train all component models and calculate ensemble weights.
        
        Args:
            data: Historical price data with datetime index
            target_column: Name of the target column to predict
        """
        try:
            self.logger.info(f"Training ensemble with {len(self.component_models)} component models")
            
            # Split data for validation-based weighting
            split_idx = int(len(data) * (1 - self.validation_split))
            train_data = data.iloc[:split_idx]
            val_data = data.iloc[split_idx:]
            
            # Train component models in parallel
            with ThreadPoolExecutor(max_workers=min(len(self.component_models), 4)) as executor:
                future_to_model = {
                    executor.submit(self._train_model, model, train_data, target_column): model 
                    for model in self.component_models
                }
                
                trained_models = []
                for future in as_completed(future_to_model):
                    model = future_to_model[future]
                    try:
                        success = future.result()
                        if success:
                            trained_models.append(model)
                    except Exception as e:
                        self.logger.error(f"Error training {model.model_name}: {e}")
            
            self.component_models = trained_models
            
            if not self.component_models:
                raise ValueError("No component models trained successfully")
            
            # Calculate model weights based on validation performance
            if len(val_data) > 10:  # Only if we have enough validation data
                self._calculate_ensemble_weights(val_data, target_column)
            else:
                # Equal weighting if insufficient validation data
                self.model_weights = {
                    model.model_name: 1.0 / len(self.component_models) 
                    for model in self.component_models
                }
            
            self.is_fitted = True
            
            # Calculate ensemble training metrics
            self._calculate_ensemble_metrics(train_data, target_column)
            
            self.logger.info(f"Ensemble model trained with weights: {self.model_weights}")
            
        except Exception as e:
            self.logger.error(f"Error training ensemble model: {e}")
            raise
    
    def _train_model(self, model: BaseModel, data: pd.DataFrame, target_column: str) -> bool:
        """Train a single component model."""
        try:
            model.fit(data, target_column)
            return True
        except Exception as e:
            self.logger.error(f"Failed to train {model.model_name}: {e}")
            return False
    
    def _calculate_ensemble_weights(self, validation_data: pd.DataFrame, target_column: str) -> None:
        """Calculate optimal weights for component models based on validation performance."""
        model_performances = {}
        
        for model in self.component_models:
            try:
                metrics = model.validate(validation_data, target_column)
                # Use inverse of MAE as performance score (lower MAE = better performance)
                performance_score = 1.0 / (metrics.get('mae', 1.0) + 1e-8)
                model_performances[model.model_name] = performance_score
                self.component_metrics[model.model_name] = metrics
            except Exception as e:
                self.logger.warning(f"Error validating {model.model_name}: {e}")
                model_performances[model.model_name] = 0.1  # Low weight for failed models
        
        if self.weighting_method == 'equal':
            # Equal weighting
            self.model_weights = {
                name: 1.0 / len(self.component_models) 
                for name in model_performances.keys()
            }
        elif self.weighting_method == 'performance':
            # Performance-based weighting
            total_performance = sum(model_performances.values())
            self.model_weights = {
                name: perf / total_performance 
                for name, perf in model_performances.items()
            }
        elif self.weighting_method == 'adaptive':
            # Adaptive weighting with minimum allocation
            min_weight = 0.1
            adjusted_performances = {}
            
            for name, perf in model_performances.items():
                adjusted_performances[name] = max(perf, min_weight * sum(model_performances.values()))
            
            total_adjusted = sum(adjusted_performances.values())
            self.model_weights = {
                name: perf / total_adjusted 
                for name, perf in adjusted_performances.items()
            }
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Generate ensemble forecasts by combining component model predictions.
        
        Args:
            periods: Number of periods to forecast
            confidence_interval: Confidence level for prediction intervals
            
        Returns:
            DataFrame with ensemble predictions and confidence bounds
        """
        if not self.is_fitted:
            raise ValueError("Ensemble model must be fitted before making predictions")
        
        try:
            component_predictions = {}
            
            # Get predictions from each component model
            for model in self.component_models:
                try:
                    pred = model.predict(periods, confidence_interval)
                    component_predictions[model.model_name] = pred
                except Exception as e:
                    self.logger.warning(f"Error getting predictions from {model.model_name}: {e}")
            
            if not component_predictions:
                raise ValueError("No component models provided predictions")
            
            # Combine predictions using weighted average
            ensemble_pred = self._combine_predictions(component_predictions, confidence_interval)
            
            self.logger.info(f"Generated ensemble forecast for {periods} periods")
            return ensemble_pred
            
        except Exception as e:
            self.logger.error(f"Error generating ensemble predictions: {e}")
            raise
    
    def _combine_predictions(self, predictions: Dict[str, pd.DataFrame], 
                           confidence_interval: float) -> pd.DataFrame:
        """Combine component predictions using ensemble weights."""
        
        # Get common time index
        common_index = None
        for pred_df in predictions.values():
            if common_index is None:
                common_index = pred_df.index
            else:
                common_index = common_index.intersection(pred_df.index)
        
        if len(common_index) == 0:
            raise ValueError("No common prediction periods among component models")
        
        # Initialize ensemble arrays
        ensemble_prices = np.zeros(len(common_index))
        ensemble_lower = np.zeros(len(common_index))
        ensemble_upper = np.zeros(len(common_index))
        
        # Weighted combination
        total_weight = 0
        for model_name, pred_df in predictions.items():
            weight = self.model_weights.get(model_name, 0)
            if weight > 0:
                pred_aligned = pred_df.loc[common_index]
                
                ensemble_prices += weight * pred_aligned['predicted_price'].values
                ensemble_lower += weight * pred_aligned.get('lower_bound', pred_aligned['predicted_price']).values
                ensemble_upper += weight * pred_aligned.get('upper_bound', pred_aligned['predicted_price']).values
                
                total_weight += weight
        
        # Normalize if weights don't sum to 1
        if total_weight > 0 and abs(total_weight - 1.0) > 1e-6:
            ensemble_prices /= total_weight
            ensemble_lower /= total_weight
            ensemble_upper /= total_weight
        
        # Adjust confidence bounds for ensemble uncertainty
        ensemble_std = np.std([pred_df.loc[common_index]['predicted_price'].values 
                              for pred_df in predictions.values()], axis=0)
        
        confidence_multiplier = 1.96 if confidence_interval == 0.95 else 2.58  # Basic approximation
        
        ensemble_lower = np.minimum(ensemble_lower, 
                                   ensemble_prices - confidence_multiplier * ensemble_std)
        ensemble_upper = np.maximum(ensemble_upper, 
                                   ensemble_prices + confidence_multiplier * ensemble_std)
        
        # Create result DataFrame
        result = pd.DataFrame({
            'predicted_price': ensemble_prices,
            'lower_bound': ensemble_lower,
            'upper_bound': ensemble_upper,
            'model': 'Ensemble'
        }, index=common_index)
        
        return result
    
    def validate(self, validation_data: pd.DataFrame, target_column: str = 'close') -> Dict[str, float]:
        """
        Validate the ensemble model on out-of-sample data.
        
        Args:
            validation_data: Validation dataset
            target_column: Target column name
            
        Returns:
            Dictionary of validation metrics
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before validation")
        
        try:
            # This is a simplified validation - in practice, you'd need to implement
            # proper ensemble validation with the same combination logic
            component_metrics = []
            
            for model in self.component_models:
                try:
                    metrics = model.validate(validation_data, target_column)
                    component_metrics.append(metrics)
                except Exception as e:
                    self.logger.warning(f"Error validating {model.model_name}: {e}")
            
            if not component_metrics:
                return {'error': 'No component models validated successfully'}
            
            # Combine metrics using weighted average
            combined_metrics = {}
            for metric_name in ['mae', 'mse', 'rmse', 'r2', 'mape']:
                metric_values = []
                weights = []
                
                for i, metrics in enumerate(component_metrics):
                    if metric_name in metrics:
                        metric_values.append(metrics[metric_name])
                        model_name = self.component_models[i].model_name
                        weights.append(self.model_weights.get(model_name, 1.0))
                
                if metric_values:
                    combined_metrics[metric_name] = np.average(metric_values, weights=weights)
            
            self.logger.info(f"Ensemble validation completed. MAE: {combined_metrics.get('mae', 0):.4f}")
            return combined_metrics
            
        except Exception as e:
            self.logger.error(f"Error during ensemble validation: {e}")
            return {}
    
    def _calculate_ensemble_metrics(self, data: pd.DataFrame, target_column: str) -> None:
        """Calculate training metrics for the ensemble."""
        try:
            # Generate in-sample predictions for metrics calculation
            predictions = self.predict(periods=min(30, len(data) // 4))
            
            # This is simplified - in practice you'd align with actual data
            self.training_metrics = {
                'component_models': len(self.component_models),
                'model_weights': self.model_weights,
                'ensemble_method': self.weighting_method
            }
            
        except Exception as e:
            self.logger.warning(f"Error calculating ensemble metrics: {e}")
    
    def get_component_performance(self) -> Dict[str, Dict]:
        """Get performance metrics for all component models."""
        return self.component_metrics
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current model weights."""
        return self.model_weights.copy() if self.model_weights else {}
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Update model weights manually."""
        # Normalize weights to sum to 1
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            self.model_weights = {
                name: weight / total_weight 
                for name, weight in new_weights.items()
            }
            self.logger.info(f"Updated model weights: {self.model_weights}")
