"""
Control Panel for Asset Selection and Model Configuration
========================================================

Provides user interface controls for selecting assets, configuring models,
and initiating forecasting operations.
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
import logging

from utils.config import config

class ControlPanel(ttk.Frame):
    """Control panel widget for asset selection and model configuration."""
    
    def __init__(self, parent, asset_change_callback: Callable, forecast_callback: Callable):
        """
        Initialize the control panel.
        
        Args:
            parent: Parent widget
            asset_change_callback: Callback for asset selection changes
            forecast_callback: Callback for forecast generation requests
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.asset_change_callback = asset_change_callback
        self.forecast_callback = forecast_callback
        
        # State variables
        self.current_data_info = {}
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all control panel widgets."""
        # Title
        title_label = ttk.Label(self, text="Financial Forecaster", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # Asset Selection Section
        self.create_asset_selection()
        
        # Data Information Section
        self.create_data_info()
        
        # Model Configuration Section
        self.create_model_config()
        
        # Forecast Configuration Section
        self.create_forecast_config()
        
        # Action Buttons Section
        self.create_action_buttons()
    
    def create_asset_selection(self):
        """Create asset selection controls."""
        # Asset Selection Frame
        asset_frame = ttk.LabelFrame(self, text="Asset Selection", padding=10)
        asset_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Asset Type Selection
        ttk.Label(asset_frame, text="Asset Type:").pack(anchor=tk.W)
        
        self.asset_type_var = tk.StringVar(value="forex")
        asset_types = ["forex", "crypto", "stock"]
        
        self.asset_type_combo = ttk.Combobox(
            asset_frame, 
            textvariable=self.asset_type_var,
            values=asset_types,
            state="readonly"
        )
        self.asset_type_combo.pack(fill=tk.X, pady=(5, 10))
        self.asset_type_combo.bind('<<ComboboxSelected>>', self.on_asset_type_change)
        
        # Symbol Selection
        ttk.Label(asset_frame, text="Symbol:").pack(anchor=tk.W)
        
        self.symbol_var = tk.StringVar(value="EURUSD")
        self.symbol_combo = ttk.Combobox(
            asset_frame,
            textvariable=self.symbol_var,
            state="readonly"
        )
        self.symbol_combo.pack(fill=tk.X, pady=(5, 10))
        self.symbol_combo.bind('<<ComboboxSelected>>', self.on_symbol_change)
        
        # Populate initial symbols
        self.update_symbol_list()
        
        # Time Range Selection
        ttk.Label(asset_frame, text="Data Range:").pack(anchor=tk.W)
        
        self.time_range_var = tk.StringVar(value="1 Year")
        time_ranges = ["6 Months", "1 Year", "2 Years", "5 Years"]
        
        self.time_range_combo = ttk.Combobox(
            asset_frame,
            textvariable=self.time_range_var,
            values=time_ranges,
            state="readonly"
        )
        self.time_range_combo.pack(fill=tk.X, pady=(5, 0))
        self.time_range_combo.bind('<<ComboboxSelected>>', self.on_time_range_change)
    
    def create_data_info(self):
        """Create data information display."""
        info_frame = ttk.LabelFrame(self, text="Data Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Data info labels
        self.data_points_label = ttk.Label(info_frame, text="Data Points: N/A")
        self.data_points_label.pack(anchor=tk.W)
        
        self.date_range_label = ttk.Label(info_frame, text="Date Range: N/A")
        self.date_range_label.pack(anchor=tk.W)
        
        self.last_price_label = ttk.Label(info_frame, text="Last Price: N/A")
        self.last_price_label.pack(anchor=tk.W)
        
        self.price_change_label = ttk.Label(info_frame, text="24h Change: N/A")
        self.price_change_label.pack(anchor=tk.W)
    
    def create_model_config(self):
        """Create model configuration controls."""
        model_frame = ttk.LabelFrame(self, text="Model Configuration", padding=10)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Model Type Selection
        ttk.Label(model_frame, text="Model Type:").pack(anchor=tk.W)
        
        self.model_type_var = tk.StringVar(value="Ensemble")
        model_types = ["Ensemble", "Prophet", "LSTM"]
        
        self.model_type_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_type_var,
            values=model_types,
            state="readonly"
        )
        self.model_type_combo.pack(fill=tk.X, pady=(5, 10))
        
        # Advanced Settings Button
        self.advanced_settings_btn = ttk.Button(
            model_frame,
            text="Advanced Settings...",
            command=self.show_advanced_settings,
            state=tk.DISABLED  # Disabled for now
        )
        self.advanced_settings_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Model Status
        self.model_status_label = ttk.Label(model_frame, text="Status: No model trained")
        self.model_status_label.pack(anchor=tk.W)
    
    def create_forecast_config(self):
        """Create forecast configuration controls."""
        forecast_frame = ttk.LabelFrame(self, text="Forecast Configuration", padding=10)
        forecast_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Forecast Periods
        ttk.Label(forecast_frame, text="Forecast Periods:").pack(anchor=tk.W)
        
        periods_frame = ttk.Frame(forecast_frame)
        periods_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.periods_var = tk.IntVar(value=30)
        self.periods_spinbox = tk.Spinbox(
            periods_frame,
            from_=1,
            to=365,
            textvariable=self.periods_var,
            width=10
        )
        self.periods_spinbox.pack(side=tk.LEFT)
        
        ttk.Label(periods_frame, text=" days").pack(side=tk.LEFT)
        
        # Confidence Interval
        ttk.Label(forecast_frame, text="Confidence Level:").pack(anchor=tk.W)
        
        confidence_frame = ttk.Frame(forecast_frame)
        confidence_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.confidence_var = tk.DoubleVar(value=0.95)
        confidence_values = [0.90, 0.95, 0.99]
        
        for conf in confidence_values:
            ttk.Radiobutton(
                confidence_frame,
                text=f"{conf*100:.0f}%",
                variable=self.confidence_var,
                value=conf
            ).pack(side=tk.LEFT, padx=(0, 10))
    
    def create_action_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Train Model Button
        self.train_btn = ttk.Button(
            button_frame,
            text="🤖 Train Model",
            command=self.on_train_model
        )
        self.train_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Generate Forecast Button
        self.forecast_btn = ttk.Button(
            button_frame,
            text="📈 Generate Forecast",
            command=self.on_generate_forecast,
            state=tk.DISABLED
        )
        self.forecast_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Refresh Data Button
        self.refresh_btn = ttk.Button(
            button_frame,
            text="🔄 Refresh Data",
            command=self.on_refresh_data
        )
        self.refresh_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Model Performance Button
        self.performance_btn = ttk.Button(
            button_frame,
            text="📊 View Performance",
            command=self.on_view_performance,
            state=tk.DISABLED
        )
        self.performance_btn.pack(fill=tk.X)
    
    def on_asset_type_change(self, event=None):
        """Handle asset type selection change."""
        self.update_symbol_list()
        self.on_symbol_change()
    
    def on_symbol_change(self, event=None):
        """Handle symbol selection change."""
        if self.asset_change_callback:
            symbol = self.symbol_var.get()
            asset_type = self.asset_type_var.get()
            self.asset_change_callback(symbol, asset_type)
    
    def on_time_range_change(self, event=None):
        """Handle time range change."""
        # Trigger data refresh with new time range
        self.on_refresh_data()
    
    def update_symbol_list(self):
        """Update the symbol dropdown based on selected asset type."""
        asset_type = self.asset_type_var.get()
        
        # Get symbols from configuration
        supported_assets = config.get_supported_assets()
        symbols = supported_assets.get(asset_type, [])
        
        if not symbols:
            # Fallback symbols if config not available
            if asset_type == "forex":
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
            elif asset_type == "crypto":
                symbols = ["bitcoin", "ethereum", "cardano", "polkadot", "chainlink"]
            elif asset_type == "stock":
                symbols = ["SPY", "QQQ", "IWM", "GLD", "TLT"]
        
        self.symbol_combo['values'] = symbols
        
        if symbols and (self.symbol_var.get() not in symbols):
            self.symbol_var.set(symbols[0])
    
    def on_train_model(self):
        """Handle train model button click."""
        try:
            # Import here to avoid circular imports
            from gui.main_window import FinancialForecasterApp
            
            # Get the main application instance
            app = self.winfo_toplevel()
            if hasattr(app, 'train_model'):
                app.train_model()
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
    
    def on_generate_forecast(self):
        """Handle generate forecast button click."""
        if self.forecast_callback:
            periods = self.periods_var.get()
            confidence = self.confidence_var.get()
            self.forecast_callback(periods, confidence)
    
    def on_refresh_data(self):
        """Handle refresh data button click."""
        if self.asset_change_callback:
            symbol = self.symbol_var.get()
            asset_type = self.asset_type_var.get()
            self.asset_change_callback(symbol, asset_type)
    
    def on_view_performance(self):
        """Handle view performance button click."""
        try:
            # Get the main application instance and switch to performance tab
            app = self.winfo_toplevel()
            if hasattr(app, 'show_model_performance'):
                app.show_model_performance()
        except Exception as e:
            self.logger.error(f"Error viewing performance: {e}")
    
    def show_advanced_settings(self):
        """Show advanced model settings dialog."""
        # Placeholder for advanced settings dialog
        tk.messagebox.showinfo("Advanced Settings", 
            "Advanced model settings would be implemented here.")
    
    def update_data_info(self, data: pd.DataFrame):
        """Update data information display."""
        try:
            # Calculate data statistics
            data_points = len(data)
            start_date = data.index[0].strftime('%Y-%m-%d')
            end_date = data.index[-1].strftime('%Y-%m-%d')
            
            # Get price column
            price_col = 'close' if 'close' in data.columns else 'price'
            last_price = data[price_col].iloc[-1]
            
            # Calculate 24h change if possible
            if len(data) > 1:
                prev_price = data[price_col].iloc[-2]
                price_change = ((last_price - prev_price) / prev_price) * 100
                change_text = f"{price_change:+.2f}%"
                change_color = "green" if price_change >= 0 else "red"
            else:
                change_text = "N/A"
                change_color = "black"
            
            # Update labels
            self.data_points_label.config(text=f"Data Points: {data_points}")
            self.date_range_label.config(text=f"Date Range: {start_date} to {end_date}")
            self.last_price_label.config(text=f"Last Price: {last_price:.4f}")
            self.price_change_label.config(text=f"24h Change: {change_text}", foreground=change_color)
            
            # Store data info
            self.current_data_info = {
                'data_points': data_points,
                'start_date': start_date,
                'end_date': end_date,
                'last_price': last_price
            }
            
        except Exception as e:
            self.logger.error(f"Error updating data info: {e}")
    
    def update_model_status(self, status: str, enable_forecast: bool = False):
        """Update model status and enable/disable forecast button."""
        self.model_status_label.config(text=f"Status: {status}")
        
        # Update button states
        if enable_forecast:
            self.forecast_btn.config(state=tk.NORMAL)
            self.performance_btn.config(state=tk.NORMAL)
        else:
            self.forecast_btn.config(state=tk.DISABLED)
            self.performance_btn.config(state=tk.DISABLED)
    
    def get_current_selection(self) -> Dict:
        """Get current asset and configuration selection."""
        return {
            'symbol': self.symbol_var.get(),
            'asset_type': self.asset_type_var.get(),
            'time_range': self.time_range_var.get(),
            'model_type': self.model_type_var.get(),
            'forecast_periods': self.periods_var.get(),
            'confidence_level': self.confidence_var.get()
        }
