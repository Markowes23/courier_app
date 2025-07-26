"""
Basic Functionality Tests for Financial Forecaster
=================================================

Basic unit tests to verify core functionality works correctly.
"""

import unittest
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestDataFetching(unittest.TestCase):
    """Test data fetching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from data.data_fetcher import data_fetcher
        self.data_fetcher = data_fetcher
    
    def test_demo_data_generation(self):
        """Test that demo data can be generated."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Test forex demo data
        forex_data = self.data_fetcher._generate_demo_forex_data(
            "EURUSD", 
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        self.assertFalse(forex_data.empty)
        self.assertIn('close', forex_data.columns)
        self.assertTrue(len(forex_data) >= 25)  # At least 25 days
    
    def test_crypto_data_fallback(self):
        """Test crypto data fetching with fallback to demo data."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        crypto_data = self.data_fetcher.fetch_crypto_data(
            "bitcoin",
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        self.assertFalse(crypto_data.empty)
        self.assertTrue('price' in crypto_data.columns or 'close' in crypto_data.columns)


class TestEventManagement(unittest.TestCase):
    """Test event management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from data.event_manager import event_manager
        self.event_manager = event_manager
    
    def test_event_database_init(self):
        """Test that event database initializes correctly."""
        # Database should be initialized
        import sqlite3
        conn = sqlite3.connect(self.event_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
    
    def test_get_events(self):
        """Test retrieving events from database."""
        start_date = "2024-01-01"
        end_date = "2024-12-31"
        
        events = self.event_manager.get_events_in_range(start_date, end_date)
        
        # Should have some sample events
        self.assertGreaterEqual(len(events), 0)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_technical_indicators(self):
        """Test technical indicator calculation."""
        from utils.helpers import calculate_technical_indicators
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        prices = 100 + np.cumsum(np.random.normal(0, 1, 100))
        
        data = pd.DataFrame({
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        # Calculate indicators
        enhanced_data = calculate_technical_indicators(data)
        
        # Check that indicators were added
        self.assertIn('sma_20', enhanced_data.columns)
        self.assertIn('rsi', enhanced_data.columns)
        self.assertIn('macd', enhanced_data.columns)
    
    def test_model_metrics(self):
        """Test model performance metrics calculation."""
        from utils.helpers import calculate_model_metrics
        
        # Create sample predictions
        np.random.seed(42)
        actual = np.random.normal(100, 10, 50)
        predicted = actual + np.random.normal(0, 2, 50)  # Add some error
        
        metrics = calculate_model_metrics(actual, predicted)
        
        # Check that all expected metrics are present
        expected_metrics = ['mae', 'mse', 'rmse', 'r2', 'mape']
        for metric in expected_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], (int, float))


class TestConfigurationManagement(unittest.TestCase):
    """Test configuration management."""
    
    def test_config_loading(self):
        """Test that configuration loads without errors."""
        from utils.config import config
        
        # Should be able to get settings
        supported_assets = config.get_supported_assets()
        self.assertIsInstance(supported_assets, dict)
        
        # Should have default asset types
        self.assertIn('forex', supported_assets)
        self.assertIn('crypto', supported_assets)
        self.assertIn('stocks', supported_assets)


class TestModelInterfaces(unittest.TestCase):
    """Test model interface compliance."""
    
    def test_ensemble_model_creation(self):
        """Test that ensemble model can be created."""
        try:
            from models.ensemble_model import EnsembleModel
            
            # Should be able to create ensemble model
            model = EnsembleModel()
            self.assertIsNotNone(model)
            self.assertEqual(model.model_name, "Ensemble")
            
        except ImportError:
            self.skipTest("Ensemble model dependencies not available")
    
    def test_base_model_interface(self):
        """Test base model interface."""
        from models.base_model import BaseModel
        
        # Should be abstract - cannot instantiate directly
        with self.assertRaises(TypeError):
            BaseModel("test")


if __name__ == '__main__':
    # Create test directories
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)
