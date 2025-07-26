"""
Financial Forecaster - Main Entry Point
======================================

Advanced ML-Powered Price Prediction Tool for Financial Markets

This application provides:
- Multi-source data ingestion (Alpha Vantage, CoinGecko, Yahoo Finance, FRED)
- Machine learning forecasting models (Prophet, LSTM, Ensemble)
- Interactive GUI with real-time charts and event overlays
- Comprehensive event analysis and economic calendar integration
- Professional-grade model validation and performance metrics

Usage:
    python main.py

Requirements:
    - Python 3.8+
    - All dependencies listed in requirements.txt
    - Optional: API keys for enhanced data access (see config.ini)

Author: Senior Software Engineer & Quant Analyst
Version: 1.0.0
"""

import sys
import os
import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """Setup application environment and dependencies."""
    try:
        # Create necessary directories
        directories = ['data', 'data/cache', 'models', 'logs']
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/financial_forecaster.log'),
                logging.StreamHandler()
            ]
        )
        
        return True
        
    except Exception as e:
        print(f"Error setting up environment: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    # Critical dependencies
    critical_deps = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('matplotlib', 'matplotlib'),
        ('sklearn', 'scikit-learn'),
        ('requests', 'requests'),
        ('yfinance', 'yfinance')
    ]
    
    for module_name, package_name in critical_deps:
        try:
            __import__(module_name)
        except ImportError:
            missing_deps.append(package_name)
    
    # Optional dependencies (with warnings)
    optional_deps = [
        ('prophet', 'prophet'),
        ('tensorflow', 'tensorflow')
    ]
    
    missing_optional = []
    for module_name, package_name in optional_deps:
        try:
            __import__(module_name)
        except ImportError:
            missing_optional.append(package_name)
    
    if missing_deps:
        error_msg = f"""
Missing critical dependencies: {', '.join(missing_deps)}

Please install with:
pip install {' '.join(missing_deps)}

Or install all dependencies with:
pip install -r requirements.txt
"""
        print(error_msg)
        if 'tkinter' not in missing_deps:
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Missing Dependencies", error_msg)
                root.destroy()
            except:
                pass
        return False
    
    if missing_optional:
        warning_msg = f"""
Warning: Optional dependencies not found: {', '.join(missing_optional)}

Some features may be limited. To install all features:
pip install -r requirements.txt
"""
        print(warning_msg)
    
    return True

def main():
    """Main application entry point."""
    print("="*60)
    print("Financial Forecaster - Advanced ML Price Prediction Tool")
    print("="*60)
    print()
    
    # Setup environment
    print("Setting up application environment...")
    if not setup_environment():
        print("❌ Failed to setup environment")
        return 1
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        print("❌ Missing critical dependencies")
        return 1
    
    print("✅ All critical dependencies available")
    print()
    
    try:
        # Import and start the GUI application
        from gui.main_window import FinancialForecasterApp
        
        print("🚀 Starting Financial Forecaster GUI...")
        print()
        print("Features available:")
        print("  📊 Real-time financial data (Forex, Crypto, Stocks)")
        print("  🤖 Machine Learning models (Prophet, LSTM, Ensemble)")
        print("  📈 Interactive charts with event overlays")
        print("  📅 Economic calendar integration")
        print("  💾 Model persistence and performance tracking")
        print()
        
        # Create and run the application
        app = FinancialForecasterApp()
        app.run()
        
        print("Application closed successfully")
        return 0
        
    except ImportError as e:
        error_msg = f"Error importing application modules: {e}"
        print(f"❌ {error_msg}")
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Import Error", error_msg)
            root.destroy()
        except:
            pass
        
        return 1
    
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"❌ {error_msg}")
        logging.error(error_msg, exc_info=True)
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Application Error", error_msg)
            root.destroy()
        except:
            pass
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
