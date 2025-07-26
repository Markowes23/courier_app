"""
LSTM Neural Network Model for Financial Forecasting
===================================================

Implementation of Long Short-Term Memory neural network for time series
forecasting with technical indicators and sequence learning.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

from models.base_model import BaseModel
from utils.helpers import calculate_model_metrics, calculate_technical_indicators

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow not available. Install with: pip install tensorflow")

class LSTMModel(BaseModel):
    """LSTM neural network model for financial time series forecasting."""
    
    def __init__(self, sequence_length: int = 60, **kwargs):
        """
        Initialize LSTM model with custom parameters.
        
        Args:
            sequence_length: Number of time steps to look back
            **kwargs: Additional model parameters
        """
        super().__init__("LSTM")
        
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow library not available")
        
        self.sequence_length = sequence_length
        self.lstm_units = kwargs.get('lstm_units', [50, 50])
        self.dropout_rate = kwargs.get('dropout_rate', 0.2)
        self.learning_rate = kwargs.get('learning_rate', 0.001)
        self.batch_size = kwargs.get('batch_size', 32)
        self.epochs = kwargs.get('epochs', 100)
        self.patience = kwargs.get('patience', 15)
        
        # Scalers for features and target
        self.feature_scaler = StandardScaler()
        self.target_scaler = MinMaxScaler()
        
        self.model = None
        self.training_history = None
        self.last_sequence = None
    
    def _prepare_sequences(self, data: pd.DataFrame, target_column: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training.
        
        Args:
            data: Input data with features
            target_column: Target column name
            
        Returns:
            Tuple of (X_sequences, y_targets)
        """
        # Calculate technical indicators
        data_with_indicators = calculate_technical_indicators(data)
        
        # Select feature columns (exclude target and non-numeric columns)
        feature_cols = [col for col in data_with_indicators.columns 
                       if col != target_column and data_with_indicators[col].dtype in ['float64', 'int64']]
        
        # Remove columns with too many NaN values
        feature_cols = [col for col in feature_cols 
                       if data_with_indicators[col].notna().sum() > len(data_with_indicators) * 0.7]
        
        self.feature_columns = feature_cols
        
        # Prepare features and target
        features = data_with_indicators[feature_cols].fillna(method='ffill').fillna(method='bfill')
        target = data_with_indicators[target_column].fillna(method='ffill')
        
        # Scale the data
        features_scaled = self.feature_scaler.fit_transform(features)
        target_scaled = self.target_scaler.fit_transform(target.values.reshape(-1, 1)).flatten()
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(features_scaled)):
            X.append(features_scaled[i-self.sequence_length:i])
            y.append(target_scaled[i])
        
        return np.array(X), np.array(y)
    
    def _build_model(self, input_shape: Tuple[int, int]) -> None:
        """
        Build the LSTM neural network architecture.
        
        Args:
            input_shape: Shape of input sequences (timesteps, features)
        """
        model = Sequential()
        
        # First LSTM layer with return sequences
        model.add(LSTM(units=self.lstm_units[0], 
                      return_sequences=len(self.lstm_units) > 1,
                      input_shape=input_shape))
        model.add(Dropout(self.dropout_rate))
        model.add(BatchNormalization())
        
        # Additional LSTM layers
        for i, units in enumerate(self.lstm_units[1:], 1):
            return_sequences = i < len(self.lstm_units) - 1
            model.add(LSTM(units=units, return_sequences=return_sequences))
            model.add(Dropout(self.dropout_rate))
            model.add(BatchNormalization())
        
        # Dense layers
        model.add(Dense(25, activation='relu'))
        model.add(Dropout(self.dropout_rate))
        model.add(Dense(1))
        
        # Compile model
        optimizer = Adam(learning_rate=self.learning_rate)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        self.model = model
    
    def fit(self, data: pd.DataFrame, target_column: str = 'close') -> None:
        """
        Train the LSTM model on historical data.
        
        Args:
            data: Historical price data with datetime index
            target_column: Name of the target column to predict
        """
        try:
            self.logger.info(f"Training LSTM model on {len(data)} samples")
            
            # Prepare sequences
            X, y = self._prepare_sequences(data, target_column)
            
            if len(X) < 50:
                raise ValueError("Insufficient data for LSTM training (need at least 50 sequences)")
            
            # Split into train/validation
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Build model
            self._build_model((X.shape[1], X.shape[2]))
            
            # Define callbacks
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=self.patience, restore_best_weights=True),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=self.patience//2, min_lr=1e-7)
            ]
            
            # Train model
            history = self.model.fit(
                X_train, y_train,
                batch_size=self.batch_size,
                epochs=self.epochs,
                validation_data=(X_val, y_val),
                callbacks=callbacks,
                verbose=0
            )
            
            self.training_history = history.history
            self.is_fitted = True
            
            # Store last sequence for prediction
            self.last_sequence = X[-1]
            
            # Calculate training metrics
            train_pred = self.model.predict(X_train, verbose=0)
            train_pred_unscaled = self.target_scaler.inverse_transform(train_pred).flatten()
            y_train_unscaled = self.target_scaler.inverse_transform(y_train.reshape(-1, 1)).flatten()
            
            self.training_metrics = calculate_model_metrics(y_train_unscaled, train_pred_unscaled)
            
            self.logger.info(f"LSTM model trained successfully. R²: {self.training_metrics.get('r2', 0):.4f}")
            
        except Exception as e:
            self.logger.error(f"Error training LSTM model: {e}")
            raise
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Generate forecasts using the trained LSTM model.
        
        Args:
            periods: Number of periods to forecast
            confidence_interval: Confidence level for prediction intervals (not used in basic LSTM)
            
        Returns:
            DataFrame with predictions
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        try:
            predictions = []
            current_sequence = self.last_sequence.copy()
            
            for _ in range(periods):
                # Predict next value
                pred = self.model.predict(current_sequence.reshape(1, *current_sequence.shape), verbose=0)
                predictions.append(pred[0, 0])
                
                # Update sequence for next prediction
                # Create new row with prediction and other features (forward-filled)
                new_row = current_sequence[-1].copy()
                new_row[0] = pred[0, 0]  # Assuming first feature is the target (scaled)
                
                # Shift sequence and add new prediction
                current_sequence = np.vstack([current_sequence[1:], new_row])
            
            # Inverse transform predictions
            predictions_array = np.array(predictions).reshape(-1, 1)
            predictions_unscaled = self.target_scaler.inverse_transform(predictions_array).flatten()
            
            # Create result DataFrame
            # Note: For real implementation, you'd need to track the actual dates
            future_dates = pd.date_range(start=pd.Timestamp.now(), periods=periods, freq='D')
            
            result = pd.DataFrame({
                'timestamp': future_dates,
                'predicted_price': predictions_unscaled,
                'lower_bound': predictions_unscaled * 0.95,  # Simple confidence bounds
                'upper_bound': predictions_unscaled * 1.05,
                'model': 'LSTM'
            })
            
            result.set_index('timestamp', inplace=True)
            
            self.logger.info(f"Generated {periods} predictions with LSTM model")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating LSTM predictions: {e}")
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
            # Prepare validation sequences
            X_val, y_val = self._prepare_sequences(validation_data, target_column)
            
            if len(X_val) == 0:
                return {'error': 'Insufficient validation data'}
            
            # Generate predictions
            predictions = self.model.predict(X_val, verbose=0)
            
            # Inverse transform
            pred_unscaled = self.target_scaler.inverse_transform(predictions).flatten()
            actual_unscaled = self.target_scaler.inverse_transform(y_val.reshape(-1, 1)).flatten()
            
            # Calculate metrics
            metrics = calculate_model_metrics(actual_unscaled, pred_unscaled)
            
            self.logger.info(f"LSTM validation completed. MAE: {metrics.get('mae', 0):.4f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error during LSTM validation: {e}")
            return {}
    
    def get_training_history(self) -> Optional[Dict]:
        """Get the training history for plotting learning curves."""
        return self.training_history
