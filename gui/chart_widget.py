"""
Interactive Chart Widget for Financial Data Visualization
========================================================

Provides interactive charts for price data, forecasts, and event overlays
using matplotlib with enhanced financial chart capabilities.
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

class ChartWidget(ttk.Frame):
    """Interactive chart widget for financial data visualization."""
    
    def __init__(self, parent):
        """
        Initialize the chart widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Chart data
        self.price_data = None
        self.forecast_data = None
        self.events_data = None
        
        self.create_widgets()
        self.setup_chart_style()
    
    def create_widgets(self):
        """Create chart widgets and controls."""
        # Chart controls frame
        controls_frame = ttk.Frame(self)
        controls_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Chart type selection
        ttk.Label(controls_frame, text="Chart Type:").pack(side=tk.LEFT)
        
        self.chart_type_var = tk.StringVar(value="candlestick")
        chart_types = ["line", "candlestick", "ohlc"]
        
        self.chart_type_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.chart_type_var,
            values=chart_types,
            state="readonly",
            width=12
        )
        self.chart_type_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.chart_type_combo.bind('<<ComboboxSelected>>', self.on_chart_type_change)
        
        # Show/hide options
        self.show_events_var = tk.BooleanVar(value=True)
        self.show_forecast_var = tk.BooleanVar(value=True)
        self.show_volume_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(controls_frame, text="Events", variable=self.show_events_var,
                       command=self.refresh_chart).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(controls_frame, text="Forecast", variable=self.show_forecast_var,
                       command=self.refresh_chart).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(controls_frame, text="Volume", variable=self.show_volume_var,
                       command=self.refresh_chart).pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        ttk.Button(controls_frame, text="🔄", command=self.refresh_chart, width=3).pack(side=tk.RIGHT)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.fig.patch.set_facecolor('white')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_chart_style(self):
        """Setup matplotlib chart styling."""
        plt.style.use('default')
        
        # Set default colors and styling
        self.colors = {
            'price_line': '#2E86C1',
            'candlestick_up': '#27AE60',
            'candlestick_down': '#E74C3C',
            'forecast': '#8E44AD',
            'confidence_band': '#D5DBDB',
            'volume': '#85929E',
            'grid': '#EAEDED'
        }
    
    def update_chart(self, price_data: pd.DataFrame, events_data: Dict, forecast_data: Optional[pd.DataFrame] = None):
        """
        Update the chart with new data.
        
        Args:
            price_data: Historical price data
            events_data: Economic events data
            forecast_data: Forecast data (optional)
        """
        try:
            self.price_data = price_data
            self.events_data = events_data
            self.forecast_data = forecast_data
            
            self.refresh_chart()
            
        except Exception as e:
            self.logger.error(f"Error updating chart: {e}")
    
    def refresh_chart(self):
        """Refresh the chart with current data and settings."""
        if self.price_data is None:
            return
        
        try:
            # Clear the figure
            self.fig.clear()
            
            # Determine subplot layout
            show_volume = self.show_volume_var.get() and 'volume' in self.price_data.columns
            
            if show_volume:
                # Price chart (top) and volume chart (bottom)
                ax_price = self.fig.add_subplot(2, 1, 1)
                ax_volume = self.fig.add_subplot(2, 1, 2, sharex=ax_price)
                
                # Adjust spacing
                self.fig.subplots_adjust(hspace=0.1)
            else:
                # Price chart only
                ax_price = self.fig.add_subplot(1, 1, 1)
                ax_volume = None
            
            # Plot price data
            self.plot_price_data(ax_price)
            
            # Plot forecast if available and enabled
            if self.forecast_data is not None and self.show_forecast_var.get():
                self.plot_forecast_data(ax_price)
            
            # Plot events if available and enabled
            if self.events_data and self.show_events_var.get():
                self.plot_events(ax_price)
            
            # Plot volume if enabled
            if ax_volume is not None:
                self.plot_volume_data(ax_volume)
            
            # Format axes
            self.format_axes(ax_price, ax_volume)
            
            # Update canvas
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error refreshing chart: {e}")
    
    def plot_price_data(self, ax):
        """Plot historical price data."""
        chart_type = self.chart_type_var.get()
        
        if chart_type == "line":
            self.plot_line_chart(ax)
        elif chart_type == "candlestick":
            self.plot_candlestick_chart(ax)
        elif chart_type == "ohlc":
            self.plot_ohlc_chart(ax)
    
    def plot_line_chart(self, ax):
        """Plot simple line chart."""
        price_col = 'close' if 'close' in self.price_data.columns else 'price'
        
        ax.plot(self.price_data.index, self.price_data[price_col], 
               color=self.colors['price_line'], linewidth=1.5, label='Price')
        
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3, color=self.colors['grid'])
    
    def plot_candlestick_chart(self, ax):
        """Plot candlestick chart."""
        # Check if we have OHLC data
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in self.price_data.columns for col in required_cols):
            # Fall back to line chart
            self.plot_line_chart(ax)
            return
        
        # Simplified candlestick plotting
        for i, (date, row) in enumerate(self.price_data.iterrows()):
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            
            # Determine color
            color = self.colors['candlestick_up'] if close_price >= open_price else self.colors['candlestick_down']
            
            # Draw high-low line
            ax.plot([date, date], [low_price, high_price], color='black', linewidth=0.8)
            
            # Draw open-close body
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            # Create rectangle for the body
            width = timedelta(hours=12)  # Adjust based on data frequency
            rect = Rectangle((date - width/2, body_bottom), width, body_height,
                           facecolor=color, edgecolor='black', linewidth=0.5)
            ax.add_patch(rect)
        
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3, color=self.colors['grid'])
    
    def plot_ohlc_chart(self, ax):
        """Plot OHLC bar chart."""
        # Check if we have OHLC data
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in self.price_data.columns for col in required_cols):
            self.plot_line_chart(ax)
            return
        
        # Simplified OHLC plotting
        for date, row in self.price_data.iterrows():
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            
            # Draw high-low line
            ax.plot([date, date], [low_price, high_price], color='black', linewidth=1)
            
            # Draw open tick (left)
            tick_width = timedelta(hours=6)
            ax.plot([date - tick_width, date], [open_price, open_price], color='black', linewidth=1)
            
            # Draw close tick (right)
            ax.plot([date, date + tick_width], [close_price, close_price], color='black', linewidth=1)
        
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3, color=self.colors['grid'])
    
    def plot_forecast_data(self, ax):
        """Plot forecast data with confidence bands."""
        if 'predicted_price' not in self.forecast_data.columns:
            return
        
        # Plot forecast line
        ax.plot(self.forecast_data.index, self.forecast_data['predicted_price'],
               color=self.colors['forecast'], linewidth=2, linestyle='--', 
               label='Forecast', alpha=0.8)
        
        # Plot confidence bands if available
        if 'lower_bound' in self.forecast_data.columns and 'upper_bound' in self.forecast_data.columns:
            ax.fill_between(self.forecast_data.index,
                          self.forecast_data['lower_bound'],
                          self.forecast_data['upper_bound'],
                          color=self.colors['confidence_band'], alpha=0.3,
                          label='Confidence Band')
        
        # Add legend
        ax.legend(loc='upper left')
    
    def plot_events(self, ax):
        """Plot economic events as markers."""
        if not self.events_data or 'dates' not in self.events_data:
            return
        
        # Get y-axis limits for marker positioning
        y_min, y_max = ax.get_ylim()
        marker_y = y_max * 0.95  # Position markers near top
        
        # Plot event markers
        for i, date in enumerate(self.events_data['dates']):
            if i < len(self.events_data.get('colors', [])):
                color = self.events_data['colors'][i]
                size = self.events_data.get('sizes', [10])[i]
                title = self.events_data.get('titles', ['Event'])[i]
                
                # Plot marker
                ax.scatter([date], [marker_y], c=color, s=size*10, 
                          alpha=0.7, marker='o', edgecolors='black', linewidth=0.5)
                
                # Add text annotation (optional, can be overwhelming)
                if len(self.events_data['dates']) < 20:  # Only if not too many events
                    ax.annotate(title, (date, marker_y), 
                              xytext=(0, 10), textcoords='offset points',
                              ha='center', va='bottom', fontsize=8,
                              bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    def plot_volume_data(self, ax):
        """Plot volume data."""
        if 'volume' not in self.price_data.columns:
            return
        
        # Plot volume bars
        ax.bar(self.price_data.index, self.price_data['volume'],
               color=self.colors['volume'], alpha=0.6, width=1)
        
        ax.set_ylabel('Volume')
        ax.grid(True, alpha=0.3, color=self.colors['grid'])
        
        # Format y-axis for large numbers
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
    
    def format_axes(self, ax_price, ax_volume=None):
        """Format chart axes."""
        # Format date axis
        if ax_volume is not None:
            # Volume subplot handles x-axis
            ax_price.tick_params(labelbottom=False)
            ax_volume.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax_volume.xaxis.set_major_locator(mdates.MonthLocator())
            ax_volume.tick_params(axis='x', rotation=45)
            plt.setp(ax_volume.xaxis.get_majorticklabels(), ha='right')
        else:
            # Price subplot handles x-axis
            ax_price.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax_price.xaxis.set_major_locator(mdates.MonthLocator())
            ax_price.tick_params(axis='x', rotation=45)
            plt.setp(ax_price.xaxis.get_majorticklabels(), ha='right')
        
        # Set title
        if hasattr(self, 'current_symbol'):
            ax_price.set_title(f'{self.current_symbol} Price Chart', fontsize=14, fontweight='bold')
        
        # Adjust layout
        self.fig.tight_layout()
    
    def on_chart_type_change(self, event=None):
        """Handle chart type change."""
        self.refresh_chart()
    
    def save_chart(self, filename: str):
        """Save the current chart to file."""
        try:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Chart saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving chart: {e}")
    
    def get_chart_data(self) -> Dict:
        """Get current chart data for export."""
        return {
            'price_data': self.price_data,
            'forecast_data': self.forecast_data,
            'events_data': self.events_data,
            'chart_settings': {
                'chart_type': self.chart_type_var.get(),
                'show_events': self.show_events_var.get(),
                'show_forecast': self.show_forecast_var.get(),
                'show_volume': self.show_volume_var.get()
            }
        }
