"""
Main Application Window for Financial Forecaster
===============================================

The primary GUI window containing all application components including
charts, controls, and model management interfaces.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import threading
from pathlib import Path

from gui.chart_widget import ChartWidget
from gui.control_panel import ControlPanel
from data.data_fetcher import data_fetcher
from data.event_manager import event_manager
from models.ensemble_model import EnsembleModel
from utils.config import config
from utils.helpers import setup_logging, format_currency

class FinancialForecasterApp:
    """Main application window for the Financial Forecaster."""
    
    def __init__(self):
        """Initialize the main application window."""
        # Setup logging
        self.logger = setup_logging("INFO")
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Financial Forecaster - Advanced ML Price Prediction")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Application state
        self.current_data = None
        self.current_symbol = "EURUSD"
        self.current_asset_type = "forex"
        self.model = None
        self.is_training = False
        self.forecast_data = None
        
        # Create GUI components
        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        self.create_status_bar()
        
        # Load initial data
        self.load_initial_data()
        
        self.logger.info("Financial Forecaster application initialized")
    
    def setup_styles(self):
        """Configure application styling."""
        style = ttk.Style()
        
        # Configure theme
        try:
            style.theme_use('clam')
        except:
            pass  # Use default theme if 'clam' not available
        
        # Custom styles
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 9))
    
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Model...", command=self.load_model)
        file_menu.add_command(label="Save Model...", command=self.save_model)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data...", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Models menu
        models_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Models", menu=models_menu)
        models_menu.add_command(label="Train New Model", command=self.train_model)
        models_menu.add_command(label="Model Performance", command=self.show_model_performance)
        models_menu.add_command(label="Model Settings...", command=self.show_model_settings)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Event Manager", command=self.show_event_manager)
        tools_menu.add_command(label="Data Sources", command=self.show_data_sources)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings...", command=self.show_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_widgets(self):
        """Create the main application widgets."""
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for controls
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=0)
        
        # Control panel
        self.control_panel = ControlPanel(left_frame, self.on_asset_change, self.on_forecast_request)
        self.control_panel.pack(fill=tk.BOTH, expand=True)
        
        # Right panel for charts and analysis
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Chart notebook for multiple tabs
        self.chart_notebook = ttk.Notebook(right_frame)
        self.chart_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Price chart tab
        price_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(price_frame, text="Price Chart")
        
        self.chart_widget = ChartWidget(price_frame)
        self.chart_widget.pack(fill=tk.BOTH, expand=True)
        
        # Model performance tab
        performance_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(performance_frame, text="Model Performance")
        
        self.performance_text = tk.Text(performance_frame, wrap=tk.WORD, font=('Courier', 10))
        perf_scrollbar = ttk.Scrollbar(performance_frame, orient=tk.VERTICAL, command=self.performance_text.yview)
        self.performance_text.configure(yscrollcommand=perf_scrollbar.set)
        
        self.performance_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        perf_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Progress bar for operations
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def update_status(self, message: str, show_progress: bool = False):
        """Update the status bar message."""
        self.status_label.config(text=message)
        
        if show_progress:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
        
        self.root.update_idletasks()
    
    def on_asset_change(self, symbol: str, asset_type: str):
        """Handle asset selection change."""
        self.current_symbol = symbol
        self.current_asset_type = asset_type
        
        # Load new data in background thread
        threading.Thread(target=self.load_asset_data, daemon=True).start()
    
    def on_forecast_request(self, periods: int, confidence: float):
        """Handle forecast request."""
        if self.model is None or not self.model.is_fitted:
            messagebox.showwarning("No Model", "Please train a model first before generating forecasts.")
            return
        
        # Generate forecast in background thread
        threading.Thread(target=self.generate_forecast, args=(periods, confidence), daemon=True).start()
    
    def load_initial_data(self):
        """Load initial data for the default asset."""
        threading.Thread(target=self.load_asset_data, daemon=True).start()
    
    def load_asset_data(self):
        """Load data for the current asset."""
        try:
            self.update_status(f"Loading {self.current_symbol} data...", True)
            
            # Calculate date range (1 year history)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # Fetch data
            data = data_fetcher.fetch_data(
                self.current_symbol,
                self.current_asset_type,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if data.empty:
                self.root.after(0, lambda: messagebox.showerror("Data Error", 
                    f"No data available for {self.current_symbol}"))
                return
            
            self.current_data = data
            
            # Get events for the same period
            events = event_manager.get_events_for_chart(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Update chart on main thread
            self.root.after(0, lambda: self.update_chart(data, events))
            
            self.update_status(f"Loaded {len(data)} data points for {self.current_symbol}")
            
        except Exception as e:
            self.logger.error(f"Error loading asset data: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load data: {str(e)}"))
            self.update_status("Error loading data")
    
    def update_chart(self, data: pd.DataFrame, events: Dict):
        """Update the price chart with new data and events."""
        try:
            # Update chart widget
            self.chart_widget.update_chart(data, events, self.forecast_data)
            
            # Update control panel with data info
            self.control_panel.update_data_info(data)
            
        except Exception as e:
            self.logger.error(f"Error updating chart: {e}")
    
    def train_model(self):
        """Train a new forecasting model."""
        if self.current_data is None or len(self.current_data) < 100:
            messagebox.showwarning("Insufficient Data", 
                "Need at least 100 data points to train a model.")
            return
        
        if self.is_training:
            messagebox.showinfo("Training in Progress", 
                "Model training is already in progress.")
            return
        
        # Start training in background thread
        threading.Thread(target=self._train_model_thread, daemon=True).start()
    
    def _train_model_thread(self):
        """Train model in background thread."""
        try:
            self.is_training = True
            self.update_status("Training ensemble model...", True)
            
            # Initialize ensemble model
            self.model = EnsembleModel()
            
            # Train the model
            target_column = 'close' if 'close' in self.current_data.columns else 'price'
            self.model.fit(self.current_data, target_column)
            
            # Update performance display
            self.root.after(0, self.update_model_performance)
            
            self.update_status("Model training completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            self.root.after(0, lambda: messagebox.showerror("Training Error", 
                f"Failed to train model: {str(e)}"))
            self.update_status("Model training failed")
        finally:
            self.is_training = False
    
    def generate_forecast(self, periods: int, confidence: float):
        """Generate forecast using the trained model."""
        try:
            self.update_status(f"Generating {periods}-day forecast...", True)
            
            # Generate predictions
            forecast = self.model.predict(periods, confidence)
            self.forecast_data = forecast
            
            # Update chart with forecast
            events = event_manager.get_events_for_chart(
                self.current_data.index[0].strftime('%Y-%m-%d'),
                (datetime.now() + timedelta(days=periods)).strftime('%Y-%m-%d')
            )
            
            self.root.after(0, lambda: self.update_chart(self.current_data, events))
            
            self.update_status(f"Generated {periods}-day forecast")
            
        except Exception as e:
            self.logger.error(f"Error generating forecast: {e}")
            self.root.after(0, lambda: messagebox.showerror("Forecast Error", 
                f"Failed to generate forecast: {str(e)}"))
            self.update_status("Forecast generation failed")
    
    def update_model_performance(self):
        """Update the model performance display."""
        if self.model is None:
            return
        
        try:
            performance_text = "MODEL PERFORMANCE SUMMARY\n"
            performance_text += "=" * 50 + "\n\n"
            
            # Model information
            model_info = self.model.get_model_info()
            performance_text += f"Model Type: {model_info['model_name']}\n"
            performance_text += f"Training Status: {'Fitted' if model_info['is_fitted'] else 'Not Fitted'}\n\n"
            
            # Component model weights (for ensemble)
            if hasattr(self.model, 'get_model_weights'):
                weights = self.model.get_model_weights()
                if weights:
                    performance_text += "Component Model Weights:\n"
                    for model_name, weight in weights.items():
                        performance_text += f"  {model_name}: {weight:.3f}\n"
                    performance_text += "\n"
            
            # Training metrics
            metrics = model_info.get('training_metrics', {})
            if metrics:
                performance_text += "Training Metrics:\n"
                for metric, value in metrics.items():
                    if isinstance(value, (int, float)):
                        performance_text += f"  {metric.upper()}: {value:.4f}\n"
                performance_text += "\n"
            
            # Component performance (for ensemble)
            if hasattr(self.model, 'get_component_performance'):
                comp_perf = self.model.get_component_performance()
                if comp_perf:
                    performance_text += "Component Model Performance:\n"
                    for model_name, perf_metrics in comp_perf.items():
                        performance_text += f"\n  {model_name}:\n"
                        for metric, value in perf_metrics.items():
                            if isinstance(value, (int, float)):
                                performance_text += f"    {metric}: {value:.4f}\n"
            
            # Update text widget
            self.performance_text.delete(1.0, tk.END)
            self.performance_text.insert(1.0, performance_text)
            
        except Exception as e:
            self.logger.error(f"Error updating performance display: {e}")
    
    def save_model(self):
        """Save the trained model to file."""
        if self.model is None or not self.model.is_fitted:
            messagebox.showwarning("No Model", "No trained model to save.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Model",
            defaultextension=".pkl",
            filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                success = self.model.save_model(filename)
                if success:
                    messagebox.showinfo("Success", f"Model saved to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to save model")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save model: {str(e)}")
    
    def load_model(self):
        """Load a trained model from file."""
        filename = filedialog.askopenfilename(
            title="Load Model",
            filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.model = EnsembleModel()
                success = self.model.load_model(filename)
                if success:
                    messagebox.showinfo("Success", f"Model loaded from {filename}")
                    self.update_model_performance()
                else:
                    messagebox.showerror("Error", "Failed to load model")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load model: {str(e)}")
    
    def export_data(self):
        """Export current data and forecasts."""
        if self.current_data is None:
            messagebox.showwarning("No Data", "No data to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.csv'):
                    self.current_data.to_csv(filename)
                elif filename.endswith('.xlsx'):
                    self.current_data.to_excel(filename)
                else:
                    self.current_data.to_csv(filename)
                
                messagebox.showinfo("Success", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    # Placeholder methods for menu items
    def show_model_performance(self):
        """Show detailed model performance window."""
        self.chart_notebook.select(1)  # Switch to performance tab
    
    def show_model_settings(self):
        """Show model configuration dialog."""
        messagebox.showinfo("Model Settings", "Model settings dialog would be implemented here.")
    
    def show_event_manager(self):
        """Show event management interface."""
        messagebox.showinfo("Event Manager", "Event management interface would be implemented here.")
    
    def show_data_sources(self):
        """Show data source configuration."""
        messagebox.showinfo("Data Sources", "Data source configuration would be implemented here.")
    
    def show_settings(self):
        """Show application settings dialog."""
        messagebox.showinfo("Settings", "Application settings dialog would be implemented here.")
    
    def show_help(self):
        """Show user guide."""
        messagebox.showinfo("Help", "User guide would be implemented here.")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """Financial Forecaster v1.0

Advanced ML-Powered Price Prediction Tool

Built with:
• Prophet for seasonality and trend analysis
• LSTM neural networks for pattern recognition
• Ensemble methods for improved accuracy
• Real-time data integration
• Interactive visualizations

Developed by: Senior Software Engineer & Quant Analyst
"""
        messagebox.showinfo("About Financial Forecaster", about_text)
    
    def run(self):
        """Start the application main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.logger.info("Financial Forecaster application closed")

if __name__ == "__main__":
    app = FinancialForecasterApp()
    app.run()
