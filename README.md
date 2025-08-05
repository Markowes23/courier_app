# Financial Forecaster - Advanced ML-Powered Price Prediction Tool

## 🚀 Overview

Financial Forecaster is a comprehensive desktop application for predicting financial asset prices using advanced machine learning models. It combines multiple data sources, sophisticated forecasting algorithms, and an intuitive GUI to provide professional-grade financial analysis capabilities.

## ✨ Key Features

### 📊 **Multi-Asset Support**
- **Forex**: Major currency pairs (EUR/USD, GBP/USD, USD/JPY, etc.)
- **Cryptocurrency**: Bitcoin, Ethereum, and major altcoins
- **Stocks & ETFs**: S&P 500, NASDAQ, sector ETFs, commodities

### 🤖 **Advanced ML Models**
- **Facebook Prophet**: Excellent for seasonality and trend analysis
- **LSTM Neural Networks**: Deep learning for complex pattern recognition
- **Ensemble Methods**: Combines multiple models for improved accuracy
- **Custom Model Configuration**: Adjustable parameters and hypertuning

### 📈 **Interactive Visualizations**
- **Real-time Charts**: Candlestick, OHLC, and line charts
- **Forecast Overlays**: Confidence intervals and prediction bands
- **Event Markers**: Economic announcements and market events
- **Technical Indicators**: Moving averages, RSI, MACD, volatility

### 📅 **Economic Calendar Integration**
- **Automated Event Detection**: Fed meetings, employment reports, inflation data
- **Impact Assessment**: Visual markers based on expected market impact
- **Historical Analysis**: Correlate events with price movements
- **Custom Event Management**: Add and track your own events

### 💾 **Professional Features**
- **Model Persistence**: Save and load trained models
- **Performance Metrics**: Comprehensive validation statistics
- **Data Export**: CSV, Excel, and JSON formats
- **Caching System**: Efficient data management and offline operation

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 1GB free space

### Core Dependencies
```
pandas>=1.4.0
numpy>=1.21.0
matplotlib>=3.5.0
scikit-learn>=1.1.0
requests>=2.28.0
yfinance>=0.1.87
```

### Optional Dependencies (Enhanced Features)
```
prophet>=1.1.0          # Facebook Prophet model
tensorflow>=2.10.0      # LSTM neural networks
alpha-vantage>=2.3.1    # Enhanced forex data
fredapi>=0.5.0          # Federal Reserve economic data
```

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/financial-forecaster.git
cd financial-forecaster
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys (Optional)
Edit `config.ini` to add your API keys for enhanced data access:

```ini
[API_KEYS]
ALPHA_VANTAGE_KEY = your_alpha_vantage_key_here
FRED_API_KEY = your_fred_api_key_here
```

**Free API Keys Available:**
- **Alpha Vantage**: [Get free key](https://www.alphavantage.co/support/#api-key) (500 requests/day)
- **FRED**: [Get free key](https://fred.stlouisfed.org/docs/api/api_key.html) (Unlimited)

### 5. Run the Application
```bash
python main.py
```

## 🎯 Quick Start Guide

### 1. **Select an Asset**
- Choose asset type (Forex, Crypto, Stock)
- Select specific symbol from dropdown
- Configure data range (6 months to 5 years)

### 2. **Load Data**
- Click "🔄 Refresh Data" to fetch historical prices
- View data statistics in the information panel
- Check the interactive chart for data quality

### 3. **Train a Model**
- Click "🤖 Train Model" to start training
- Monitor progress in the status bar
- View performance metrics in the Model Performance tab

### 4. **Generate Forecasts**
- Set forecast period (1-365 days)
- Choose confidence level (90%, 95%, 99%)
- Click "📈 Generate Forecast" to predict prices

### 5. **Analyze Results**
- Review forecast accuracy and confidence bands
- Check economic events that may impact predictions
- Export data and results for further analysis

## 📚 Detailed Usage

### Data Sources and Configuration

The application automatically fetches data from multiple sources:

- **Forex Data**: Alpha Vantage API (premium) or demo data
- **Crypto Data**: CoinGecko API (free, no key required)
- **Stock Data**: Yahoo Finance via yfinance (free)
- **Economic Events**: Built-in database with major events

### Model Selection and Training

#### Prophet Model
- **Best for**: Seasonal patterns, holiday effects, trend analysis
- **Parameters**: Seasonality mode, changepoint detection, holiday effects
- **Training Time**: Fast (seconds to minutes)
- **Interpretability**: High - provides trend and seasonality components

#### LSTM Model
- **Best for**: Complex patterns, non-linear relationships
- **Parameters**: Sequence length, network architecture, learning rate
- **Training Time**: Moderate (minutes to hours)
- **Interpretability**: Low - black box neural network

#### Ensemble Model
- **Best for**: Highest accuracy, robust predictions
- **Method**: Weighted combination of Prophet and LSTM
- **Parameters**: Weighting strategy (equal, performance-based, adaptive)
- **Training Time**: Sum of component models

### Chart Features and Navigation

#### Chart Types
- **Line Chart**: Simple price line for trend analysis
- **Candlestick**: OHLC data with color-coded price movements
- **OHLC Bars**: Traditional bar chart format

#### Interactive Features
- **Zoom and Pan**: Mouse wheel and click-drag navigation
- **Event Tooltips**: Hover over markers for event details
- **Forecast Toggle**: Show/hide predictions and confidence bands
- **Volume Display**: Optional volume bars below price chart

### Performance Metrics and Validation

The application calculates comprehensive performance metrics:

#### Statistical Metrics
- **MAE (Mean Absolute Error)**: Average prediction error
- **RMSE (Root Mean Square Error)**: Penalizes large errors
- **R² (Coefficient of Determination)**: Explained variance
- **MAPE (Mean Absolute Percentage Error)**: Relative accuracy

#### Financial Metrics
- **Direction Accuracy**: Percentage of correct trend predictions
- **Volatility Ratio**: Predicted vs actual volatility
- **Maximum Drawdown**: Largest prediction error
- **Sharpe Ratio**: Risk-adjusted performance measure

## 🔧 Advanced Configuration

### Model Hyperparameters

#### Prophet Configuration
```python
prophet_params = {
    'seasonality_mode': 'multiplicative',  # or 'additive'
    'changepoint_prior_scale': 0.05,       # Trend flexibility
    'seasonality_prior_scale': 10.0,       # Seasonality strength
    'yearly_seasonality': True,
    'weekly_seasonality': True,
    'daily_seasonality': False
}
```

#### LSTM Configuration
```python
lstm_params = {
    'sequence_length': 60,        # Days of history to consider
    'lstm_units': [50, 50],      # Network architecture
    'dropout_rate': 0.2,         # Regularization
    'learning_rate': 0.001,      # Training speed
    'epochs': 100,               # Training iterations
    'batch_size': 32             # Training batch size
}
```

### Data Processing Options

#### Technical Indicators
- Simple Moving Averages (SMA): 20, 50 periods
- Exponential Moving Averages (EMA): 12, 26 periods
- Relative Strength Index (RSI): 14 periods
- MACD: 12, 26, 9 periods
- Bollinger Bands: 20 periods, 2 standard deviations

#### Feature Engineering
- Price returns and log returns
- Rolling volatility measures
- Volume-weighted average price
- Support and resistance levels
- Fibonacci retracement levels

## 📊 Data Export and Integration

### Export Formats
- **CSV**: Comma-separated values for Excel/spreadsheet analysis
- **JSON**: Structured data for programming and API integration
- **Excel**: Native Excel format with multiple sheets
- **Model Files**: Pickled models for reuse and deployment

### API Integration
The application is designed for easy integration with external systems:

```python
# Example: Programmatic model training
from models.ensemble_model import EnsembleModel
from data.data_fetcher import data_fetcher

# Fetch data
data = data_fetcher.fetch_data('EURUSD', 'forex', '2023-01-01', '2024-01-01')

# Train model
model = EnsembleModel()
model.fit(data)

# Generate forecast
forecast = model.predict(30, confidence_interval=0.95)
```

## 🧪 Testing and Validation

### Unit Tests
Run the test suite to verify functionality:
```bash
python -m pytest tests/ -v
```

### Model Validation
The application includes several validation techniques:

- **Walk-Forward Analysis**: Simulates real-world deployment
- **Cross-Validation**: K-fold validation for robustness
- **Out-of-Sample Testing**: Hold-out validation set
- **Backtesting**: Historical performance simulation

### Data Quality Checks
- Missing value detection and interpolation
- Outlier identification and treatment
- Data consistency validation
- Temporal integrity checks

## 🤝 Contributing

We welcome contributions from the community! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code style and standards
- Testing requirements
- Submission process
- Feature requests and bug reports

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Format code
black financial_forecaster/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support and Troubleshooting

### Common Issues

#### "No module named 'prophet'"
```bash
# Install Prophet (may require additional system dependencies)
pip install prophet

# On macOS with Apple Silicon:
conda install prophet -c conda-forge
```

#### "TensorFlow not available"
```bash
# Install TensorFlow
pip install tensorflow

# For GPU support:
pip install tensorflow-gpu
```

#### API Rate Limits
- Use free tier API keys for development
- Implement caching to reduce API calls
- Consider upgrading to paid tiers for production use

### Performance Optimization

#### Large Datasets
- Use data resampling for faster processing
- Implement incremental model training
- Consider cloud deployment for heavy workloads

#### Memory Usage
- Clear unused data regularly
- Use data generators for large time series
- Monitor memory usage during training

### Getting Help

1. **Documentation**: Check this README and inline code comments
2. **Issues**: Search existing GitHub issues or create a new one
3. **Discussions**: Join community discussions for general questions
4. **Email**: Contact the development team for enterprise support

## 🔮 Future Enhancements

### Planned Features
- **Web Interface**: Browser-based version for remote access
- **Mobile App**: iOS/Android companion application
- **Cloud Deployment**: AWS/Azure/GCP integration
- **Real-time Streaming**: Live data feeds and instant predictions
- **Portfolio Management**: Multi-asset portfolio optimization
- **Alert System**: Email/SMS notifications for price targets
- **Social Integration**: Share forecasts and collaborate

### Model Improvements
- **Transformer Models**: Attention-based neural networks
- **Reinforcement Learning**: Adaptive trading strategies
- **Anomaly Detection**: Unusual market condition identification
- **Sentiment Analysis**: News and social media integration
- **Alternative Data**: Satellite imagery, web scraping, IoT sensors

## 📞 Contact Information

- **Lead Developer**: Senior Software Engineer & Quant Analyst
- **Project Repository**: [GitHub Repository](https://github.com/your-username/financial-forecaster)
- **Documentation**: [Wiki Pages](https://github.com/your-username/financial-forecaster/wiki)
- **Issue Tracker**: [GitHub Issues](https://github.com/your-username/financial-forecaster/issues)

---

**Disclaimer**: This software is for educational and research purposes only. Financial predictions are inherently uncertain and should not be used as the sole basis for investment decisions. Always consult with qualified financial advisors and conduct your own research before making investment choices.

**Copyright © 2024 Financial Forecaster Development Team. All rights reserved.**
