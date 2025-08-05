"""
Configuration Manager for Financial Forecaster
==============================================

Handles API keys, settings, and configuration management with secure defaults.
"""

import configparser
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

class ConfigManager:
    """Centralized configuration management with environment variable fallbacks."""
    
    def __init__(self, config_path: str = "config.ini"):
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger(__name__)
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file with environment variable fallbacks."""
        try:
            if self.config_path.exists():
                self.config.read(self.config_path)
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.logger.warning(f"Config file {self.config_path} not found, using defaults")
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create default configuration structure."""
        self.config['API_KEYS'] = {
            'ALPHA_VANTAGE_KEY': 'demo',
            'FRED_API_KEY': 'demo'
        }
        self.config['DATA_SOURCES'] = {
            'PRICE_SOURCE': 'alpha_vantage',
            'CRYPTO_SOURCE': 'coingecko', 
            'MACRO_SOURCE': 'fred',
            'CACHE_DURATION_HOURS': '24'
        }
        self.config['MODEL_SETTINGS'] = {
            'DEFAULT_LOOKBACK_DAYS': '365',
            'DEFAULT_FORECAST_DAYS': '30',
            'RETRAIN_FREQUENCY_DAYS': '7',
            'CONFIDENCE_INTERVAL': '0.95'
        }
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key with environment variable fallback."""
        # Try environment variable first
        env_key = f"{service.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        
        if not api_key:
            # Fall back to config file
            try:
                api_key = self.config.get('API_KEYS', f"{service.upper()}_KEY", fallback=None)
            except:
                api_key = None
        
        if not api_key or api_key == 'demo':
            self.logger.warning(f"No valid API key found for {service}")
            return None
        
        return api_key
    
    def get_setting(self, section: str, key: str, fallback=None):
        """Get configuration setting with type conversion."""
        try:
            value = self.config.get(section, key, fallback=str(fallback))
            
            # Attempt type conversion for common types
            if isinstance(fallback, bool):
                return value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(fallback, int):
                return int(value)
            elif isinstance(fallback, float):
                return float(value)
            elif isinstance(fallback, list):
                return [item.strip() for item in value.split(',')]
            
            return value
        except Exception as e:
            self.logger.error(f"Error getting setting {section}.{key}: {e}")
            return fallback
    
    def get_supported_assets(self) -> Dict[str, List[str]]:
        """Get all supported asset symbols by category."""
        return {
            'forex': self.get_setting('ASSETS', 'FOREX_PAIRS', []),
            'crypto': self.get_setting('ASSETS', 'CRYPTO_SYMBOLS', []),
            'stocks': self.get_setting('ASSETS', 'STOCK_SYMBOLS', [])
        }

# Global configuration instance
config = ConfigManager()
