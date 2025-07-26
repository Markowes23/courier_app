"""
Financial Forecaster - Feature Demonstration
===========================================

This script demonstrates the key features of the Financial Forecaster application
without requiring the full GUI. It shows how to use the core components
programmatically for automated analysis and backtesting.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_demo():
    """Setup demonstration environment."""
    print("🚀 Financial Forecaster - Feature Demonstration")
    print("=" * 60)
    
    # Setup logging for demo
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("data/cache").mkdir(exist_ok=True)
    
    return True

def demo_data_fetching():
    """Demonstrate data fetching capabilities."""
    print("\n📊 DATA FETCHING DEMONSTRATION")
    print("-" * 40)
    
    try:
        from data.data_fetcher import data_fetcher
        
        # Calculate date range (6 months of data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        print("Fetching sample data for multiple asset types...")
        
        # Test different asset types
        test_assets = [
            ("EURUSD", "forex"),
            ("bitcoin", "crypto"), 
            ("SPY", "stock")
        ]
        
        results = {}
        
        for symbol, asset_type in test_assets:
            print(f"  📈 Fetching {asset_type.upper()}: {symbol}")
            
            try:
                data = data_fetcher.fetch_data(
                    symbol, asset_type,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                if not data.empty:
                    results[f"{symbol}_{asset_type}"] = data
                    print(f"    ✅ Got {len(data)} data points")
                    print(f"    📅 Range: {data.index[0].date()} to {data.index[-1].date()}")
                    
                    # Show recent prices
                    price_col = 'close' if 'close' in data.columns else 'price'
                    recent_price = data[price_col].iloc[-1]
                    print(f"    💰 Latest price: {recent_price:.4f}")
                else:
                    print(f"    ❌ No data received")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        print(f"\n✅ Successfully fetched data for {len(results)} assets")
        return results
        
    except Exception as e:
        print(f"❌ Data fetching failed: {e}")
        return {}

def demo_event_management():
    """Demonstrate economic event management."""
    print("\n📅 ECONOMIC EVENTS DEMONSTRATION")
    print("-" * 40)
    
    try:
        from data.event_manager import event_manager
        
        # Get events for the next month
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"Fetching events from {start_date} to {end_date}...")
        
        events = event_manager.get_events_in_range(start_date, end_date)
        
        if not events.empty:
            print(f"✅ Found {len(events)} upcoming events")
            print("\nUpcoming high-impact events:")
            
            high_impact = events[events['impact_level'] >= 4]
            for _, event in high_impact.head(5).iterrows():
                print(f"  🔴 {event['date']}: {event['title']}")
                print(f"     {event['description']}")
        else:
            print("📝 No upcoming events found (using sample data)")
        
        # Demonstrate event formatting for charts
        chart_events = event_manager.get_events_for_chart(start_date, end_date)
        if chart_events:
            print(f"\n📊 Chart events formatted: {len(chart_events.get('dates', []))} markers ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Event management failed: {e}")
        return False

def demo_model_training():
    """Demonstrate machine learning model training."""
    print("\n🤖 MACHINE LEARNING MODELS DEMONSTRATION")
    print("-" * 40)
    
    try:
        # Generate sample data for demonstration
        print("Generating sample financial data for model training...")
        
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        np.random.seed(42)  # Reproducible results
        
        # Generate realistic price data
        base_price = 1.0800  # EUR/USD example
        returns = np.random.normal(0.0002, 0.01, len(dates))  # Small upward bias
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create comprehensive dataset
        sample_data = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1e6, 1e7, len(dates))
        }, index=dates)
        
        print(f"✅ Generated {len(sample_data)} days of sample data")
        print(f"📊 Price range: {sample_data['close'].min():.4f} - {sample_data['close'].max():.4f}")
        
        # Test individual models
        models_to_test = []
        
        # Test Prophet model (if available)
        try:
            from models.prophet_model import ProphetModel
            models_to_test.append(("Prophet", ProphetModel))
            print("📈 Prophet model available")
        except ImportError:
            print("⚠️  Prophet model not available (install with: pip install prophet)")
        
        # Test LSTM model (if available)
        try:
            from models.lstm_model import LSTMModel
            models_to_test.append(("LSTM", LSTMModel))
            print("🧠 LSTM model available")
        except ImportError:
            print("⚠️  LSTM model not available (install with: pip install tensorflow)")
        
        # Test Ensemble model
        try:
            from models.ensemble_model import EnsembleModel
            models_to_test.append(("Ensemble", EnsembleModel))
            print("🎯 Ensemble model available")
        except ImportError:
            print("❌ Ensemble model not available")
        
        if not models_to_test:
            print("❌ No models available for testing")
            return False
        
        # Train and test models
        train_size = int(len(sample_data) * 0.8)
        train_data = sample_data.iloc[:train_size]
        test_data = sample_data.iloc[train_size:]
        
        print(f"\n🎯 Training models on {len(train_data)} samples, testing on {len(test_data)}")
        
        trained_models = {}
        
        for model_name, ModelClass in models_to_test:
            print(f"\nTraining {model_name} model...")
            
            try:
                if model_name == "LSTM":
                    # Use smaller sequence length for demo
                    model = ModelClass(sequence_length=min(30, len(train_data)//4))
                else:
                    model = ModelClass()
                
                # Train the model
                model.fit(train_data, 'close')
                print(f"  ✅ {model_name} training completed")
                
                # Validate on test data
                if len(test_data) > 10:
                    metrics = model.validate(test_data, 'close')
                    if metrics and 'mae' in metrics:
                        print(f"  📊 Validation MAE: {metrics['mae']:.6f}")
                        print(f"  📊 Validation R²: {metrics.get('r2', 0):.4f}")
                
                # Generate sample forecast
                forecast = model.predict(periods=7, confidence_interval=0.95)
                print(f"  🔮 Generated 7-day forecast")
                print(f"  📈 Predicted prices: {forecast['predicted_price'].iloc[0]:.4f} - {forecast['predicted_price'].iloc[-1]:.4f}")
                
                trained_models[model_name] = model
                
            except Exception as e:
                print(f"  ❌ {model_name} training failed: {e}")
        
        print(f"\n✅ Successfully trained {len(trained_models)} models")
        return trained_models
        
    except Exception as e:
        print(f"❌ Model training demonstration failed: {e}")
        return {}

def demo_technical_analysis():
    """Demonstrate technical analysis capabilities."""
    print("\n📊 TECHNICAL ANALYSIS DEMONSTRATION")
    print("-" * 40)
    
    try:
        from utils.helpers import calculate_technical_indicators
        
        # Generate sample OHLC data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLC data
        ohlc_data = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1e5, 1e6, len(dates))
        }, index=dates)
        
        print(f"📈 Calculating technical indicators for {len(ohlc_data)} price points...")
        
        # Calculate indicators
        enhanced_data = calculate_technical_indicators(ohlc_data)
        
        # Show available indicators
        indicators = [col for col in enhanced_data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        print(f"✅ Calculated {len(indicators)} technical indicators:")
        
        for indicator in indicators:
            if enhanced_data[indicator].notna().sum() > 0:
                latest_value = enhanced_data[indicator].dropna().iloc[-1]
                print(f"  📊 {indicator.upper()}: {latest_value:.4f}")
        
        # Demonstrate signal generation
        latest_data = enhanced_data.iloc[-1]
        signals = []
        
        if 'rsi' in enhanced_data.columns:
            rsi = latest_data['rsi']
            if rsi > 70:
                signals.append("RSI indicates overbought condition")
            elif rsi < 30:
                signals.append("RSI indicates oversold condition")
        
        if 'sma_20' in enhanced_data.columns and 'sma_50' in enhanced_data.columns:
            if latest_data['sma_20'] > latest_data['sma_50']:
                signals.append("Short-term MA above long-term MA (bullish)")
            else:
                signals.append("Short-term MA below long-term MA (bearish)")
        
        if signals:
            print(f"\n🎯 Technical signals:")
            for signal in signals:
                print(f"  📈 {signal}")
        
        return enhanced_data
        
    except Exception as e:
        print(f"❌ Technical analysis failed: {e}")
        return None

def demo_performance_metrics():
    """Demonstrate model performance calculation."""
    print("\n📊 PERFORMANCE METRICS DEMONSTRATION")
    print("-" * 40)
    
    try:
        from utils.helpers import calculate_model_metrics
        
        # Generate sample actual vs predicted data
        np.random.seed(42)
        n_samples = 100
        
        # Create realistic prediction scenario
        actual_prices = np.random.normal(100, 10, n_samples)
        # Predictions with some error
        predicted_prices = actual_prices + np.random.normal(0, 2, n_samples)
        
        print(f"📊 Calculating performance metrics for {n_samples} predictions...")
        
        metrics = calculate_model_metrics(actual_prices, predicted_prices)
        
        print("✅ Model Performance Metrics:")
        print(f"  📊 Mean Absolute Error (MAE): {metrics['mae']:.4f}")
        print(f"  📊 Root Mean Square Error (RMSE): {metrics['rmse']:.4f}")
        print(f"  📊 R-squared (R²): {metrics['r2']:.4f}")
        print(f"  📊 Mean Absolute Percentage Error (MAPE): {metrics['mape']:.2f}%")
        
        if 'direction_accuracy' in metrics:
            print(f"  🎯 Direction Accuracy: {metrics['direction_accuracy']*100:.1f}%")
        
        # Interpret results
        print(f"\n🎯 Model Assessment:")
        if metrics['r2'] > 0.8:
            print("  ✅ Excellent model performance (R² > 0.8)")
        elif metrics['r2'] > 0.6:
            print("  ✅ Good model performance (R² > 0.6)")
        elif metrics['r2'] > 0.4:
            print("  ⚠️  Moderate model performance (R² > 0.4)")
        else:
            print("  ⚠️  Model may need improvement (R² < 0.4)")
        
        if metrics['mape'] < 5:
            print("  ✅ Low prediction error (MAPE < 5%)")
        elif metrics['mape'] < 10:
            print("  ✅ Acceptable prediction error (MAPE < 10%)")
        else:
            print("  ⚠️  High prediction error (MAPE > 10%)")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Performance metrics calculation failed: {e}")
        return {}

def main():
    """Run the complete demonstration."""
    try:
        # Setup
        if not setup_demo():
            return 1
        
        print("This demonstration showcases the core capabilities of the")
        print("Financial Forecaster application without requiring the GUI.")
        print("\nRunning feature demonstrations...")
        
        # Run demonstrations
        results = {}
        
        # 1. Data Fetching
        data_results = demo_data_fetching()
        results['data_fetching'] = len(data_results) > 0
        
        # 2. Event Management
        events_result = demo_event_management()
        results['event_management'] = events_result
        
        # 3. Model Training
        models_result = demo_model_training()
        results['model_training'] = len(models_result) > 0 if isinstance(models_result, dict) else False
        
        # 4. Technical Analysis
        tech_result = demo_technical_analysis()
        results['technical_analysis'] = tech_result is not None
        
        # 5. Performance Metrics
        metrics_result = demo_performance_metrics()
        results['performance_metrics'] = len(metrics_result) > 0
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 DEMONSTRATION SUMMARY")
        print("=" * 60)
        
        successful_demos = sum(results.values())
        total_demos = len(results)
        
        print(f"✅ Completed {successful_demos}/{total_demos} feature demonstrations")
        print()
        
        for feature, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            feature_name = feature.replace('_', ' ').title()
            print(f"  {status} - {feature_name}")
        
        print()
        print("🚀 NEXT STEPS:")
        print("  1. Run 'python main.py' to start the full GUI application")
        print("  2. Install optional dependencies for enhanced features:")
        print("     pip install prophet tensorflow")
        print("  3. Configure API keys in config.ini for live data")
        print("  4. Check README.md for detailed usage instructions")
        
        if successful_demos == total_demos:
            print("\n🎊 All features working correctly! Ready for production use.")
            return 0
        else:
            print(f"\n⚠️  Some features need attention. Check error messages above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\nDemo completed with exit code: {exit_code}")
    sys.exit(exit_code)
