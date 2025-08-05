"""
Utility Functions for Financial Forecaster
==========================================

Common helper functions for data validation, transformation, and analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
import re

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup application logging with consistent formatting."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('financial_forecaster.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_symbol(symbol: str, asset_type: str = 'auto') -> bool:
    """Validate asset symbol format based on type."""
    symbol = symbol.upper().strip()
    
    if asset_type == 'forex' or (asset_type == 'auto' and len(symbol) == 6):
        # Forex pairs like EURUSD, GBPUSD
        return bool(re.match(r'^[A-Z]{6}$', symbol))
    elif asset_type == 'crypto' or (asset_type == 'auto' and symbol.lower() in ['bitcoin', 'ethereum']):
        # Crypto symbols (can be names or tickers)
        return bool(re.match(r'^[A-Za-z0-9\-]+$', symbol))
    elif asset_type == 'stock' or asset_type == 'auto':
        # Stock tickers
        return bool(re.match(r'^[A-Z]{1,5}$', symbol))
    
    return False

def clean_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate price data with comprehensive error handling."""
    logger = logging.getLogger(__name__)
    
    if df.empty:
        logger.warning("Empty dataframe provided for cleaning")
        return df
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        elif 'date' in df.columns:
            df.set_index('date', inplace=True)
        
        df.index = pd.to_datetime(df.index)
    
    # Remove duplicates and sort
    df = df[~df.index.duplicated(keep='last')].sort_index()
    
    # Handle missing values
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_columns:
        # Forward fill small gaps (up to 3 days)
        df[col] = df[col].fillna(method='ffill', limit=3)
        
        # Remove rows with still missing critical price data
        if col in ['close', 'price']:
            df = df.dropna(subset=[col])
    
    # Remove obvious outliers (more than 5 standard deviations)
    for col in numeric_columns:
        if col in ['close', 'price', 'open', 'high', 'low']:
            mean_val = df[col].mean()
            std_val = df[col].std()
            df = df[abs(df[col] - mean_val) <= 5 * std_val]
    
    # Ensure positive prices
    price_cols = ['open', 'high', 'low', 'close', 'price']
    for col in price_cols:
        if col in df.columns:
            df = df[df[col] > 0]
    
    logger.info(f"Cleaned price data: {len(df)} rows remaining")
    return df

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate common technical indicators for feature engineering."""
    if 'close' not in df.columns and 'price' not in df.columns:
        return df
    
    price_col = 'close' if 'close' in df.columns else 'price'
    df = df.copy()
    
    # Moving averages
    df['sma_20'] = df[price_col].rolling(window=20).mean()
    df['sma_50'] = df[price_col].rolling(window=50).mean()
    df['ema_12'] = df[price_col].ewm(span=12).mean()
    df['ema_26'] = df[price_col].ewm(span=26).mean()
    
    # Volatility and returns
    df['volatility_20'] = df[price_col].rolling(window=20).std()
    df['returns'] = df[price_col].pct_change()
    df['log_returns'] = np.log(df[price_col] / df[price_col].shift(1))
    
    # RSI
    delta = df[price_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    
    return df

def calculate_model_metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """Calculate comprehensive model performance metrics."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    
    metrics = {}
    
    # Basic regression metrics
    metrics['mae'] = mean_absolute_error(actual, predicted)
    metrics['mse'] = mean_squared_error(actual, predicted)
    metrics['rmse'] = np.sqrt(metrics['mse'])
    metrics['r2'] = r2_score(actual, predicted)
    
    # Financial-specific metrics
    actual_returns = np.diff(actual) / actual[:-1]
    predicted_returns = np.diff(predicted) / predicted[:-1]
    
    if len(actual_returns) > 0 and len(predicted_returns) > 0:
        # Direction accuracy
        actual_direction = np.sign(actual_returns)
        predicted_direction = np.sign(predicted_returns)
        metrics['direction_accuracy'] = np.mean(actual_direction == predicted_direction)
        
        # Volatility metrics
        metrics['actual_volatility'] = np.std(actual_returns)
        metrics['predicted_volatility'] = np.std(predicted_returns)
        metrics['volatility_ratio'] = metrics['predicted_volatility'] / metrics['actual_volatility']
    
    # Percentage errors
    metrics['mape'] = np.mean(np.abs((actual - predicted) / actual)) * 100
    
    return metrics

def format_currency(value: float, currency: str = 'USD') -> str:
    """Format currency values for display."""
    if pd.isna(value):
        return "N/A"
    
    currency_symbols = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
        'AUD': 'A$', 'CAD': 'C$', 'CHF': 'CHF', 'CNY': '¥'
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    if abs(value) >= 1e6:
        return f"{symbol}{value/1e6:.2f}M"
    elif abs(value) >= 1e3:
        return f"{symbol}{value/1e3:.2f}K"
    else:
        return f"{symbol}{value:.2f}"
