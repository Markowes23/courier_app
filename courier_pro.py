import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import threading
import json
import os
import requests
import sqlite3
import csv
from PIL import Image, ImageTk
import customtkinter as ctk
from automation_engine import TaskAutomationEngine, ContentCreationEngine, BatchOperationManager, DeliveryStop

# Built-in van capacity dataset
VAN_CAPACITY_DATA = [
    {"make": "Ford", "model": "Transit", "capacity": 11.0, "fuel_efficiency": 12.5},
    {"make": "Mercedes", "model": "Sprinter", "capacity": 13.5, "fuel_efficiency": 10.8},
    {"make": "Volkswagen", "model": "Crafter", "capacity": 14.0, "fuel_efficiency": 11.2},
    {"make": "Iveco", "model": "Daily", "capacity": 12.0, "fuel_efficiency": 13.1},
    {"make": "Renault", "model": "Master", "capacity": 13.0, "fuel_efficiency": 11.8},
]

try:
    from tkintermapview import TkinterMapView
except ImportError:
    TkinterMapView = None

class CourierProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title('CourierPro - Advanced Delivery Management Suite')
        self.geometry('1400x900')
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize data
        self.stops = []
        self.progress = 0
        self.total_capacity = 0
        self.used_capacity = 0
        self.weather_cache = {}
        self.delivery_history = []
        self.route_templates = []
        
        # Setup database
        self.setup_database()
        
        # Initialize automation engines
        self.automation_engine = TaskAutomationEngine(self.db_path)
        self.content_engine = ContentCreationEngine(self.db_path)
        self.batch_manager = BatchOperationManager(self.db_path)
        
        # Setup automation rules
        self.setup_default_automation_rules()
        
        # Initialize geocoder
        self.geolocator = Nominatim(user_agent="courierpro_v2")
        self.stop_counter = 1
        
        # Create UI
        self.create_modern_ui()
        self.load_saved_data()
        
        # Start automation monitoring
        self.start_automation_monitoring()
        
    def setup_database(self):
        """Initialize SQLite database for data persistence"""
        self.db_path = "courier_data.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                load_size REAL NOT NULL,
                delivery_time TEXT,
                status TEXT DEFAULT 'pending',
                coordinates TEXT,
                weather_temp REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                route_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_modern_ui(self):
        """Create the modern, professional UI"""
        
        # Main container with padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with title and controls
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(header_frame, text="CourierPro - Advanced Delivery Management",
                                 font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(side="left", padx=20, pady=15)
        
        # Quick action buttons
        actions_frame = ctk.CTkFrame(header_frame)
        actions_frame.pack(side="right", padx=20, pady=15)
        
        ctk.CTkButton(actions_frame, text="📊 Analytics", command=self.show_analytics,
                     width=120, height=35).pack(side="left", padx=5)
        ctk.CTkButton(actions_frame, text="📋 Templates", command=self.manage_templates,
                     width=120, height=35).pack(side="left", padx=5)
        ctk.CTkButton(actions_frame, text="📄 Export", command=self.export_data,
                     width=120, height=35).pack(side="left", padx=5)
        ctk.CTkButton(actions_frame, text="⚙ Settings", command=self.show_settings,
                     width=120, height=35).pack(side="left", padx=5)
        
        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.create_route_planning_tab()
        self.create_delivery_tracking_tab()
        self.create_fleet_management_tab()
        self.create_reports_tab()
    
    def create_route_planning_tab(self):
        """Create the route planning tab with enhanced features"""
        tab = self.notebook.add("🗺 Route Planning")
        
        # Left panel for controls
        left_panel = ctk.CTkFrame(tab)
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=10)
        left_panel.configure(width=400)
        
        # Van Configuration Section
        van_section = ctk.CTkFrame(left_panel)
        van_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(van_section, text="🚐 Vehicle Configuration",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Van selection with enhanced dropdown
        van_frame = ctk.CTkFrame(van_section)
        van_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(van_frame, text="Vehicle:").pack(anchor="w")
        self.van_var = tk.StringVar()
        van_options = [f"{v['make']} {v['model']} ({v['capacity']}m³)" for v in VAN_CAPACITY_DATA]
        self.van_dropdown = ctk.CTkOptionMenu(van_frame, values=van_options, 
                                            command=self.on_van_selected, variable=self.van_var)
        self.van_dropdown.pack(fill="x", pady=5)
        
        # Capacity display with fuel efficiency
        self.capacity_info = ctk.CTkLabel(van_section, text="Select a vehicle to see details")
        self.capacity_info.pack(pady=5)
        
        # Route Planning Section
        route_section = ctk.CTkFrame(left_panel)
        route_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(route_section, text="📍 Add Delivery Stop",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Enhanced address input with autocomplete
        address_frame = ctk.CTkFrame(route_section)
        address_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(address_frame, text="Address:").pack(anchor="w")
        self.address_entry = ctk.CTkEntry(address_frame, placeholder_text="Enter delivery address...")
        self.address_entry.pack(fill="x", pady=5)
        
        # Time and load inputs side by side
        inputs_frame = ctk.CTkFrame(route_section)
        inputs_frame.pack(fill="x", padx=10, pady=5)
        
        time_frame = ctk.CTkFrame(inputs_frame)
        time_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(time_frame, text="Est. Time (min):").pack(anchor="w")
        self.time_entry = ctk.CTkEntry(time_frame, placeholder_text="Auto")
        self.time_entry.pack(fill="x", pady=5)
        
        load_frame = ctk.CTkFrame(inputs_frame)
        load_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(load_frame, text="Load (m³):").pack(anchor="w")
        self.load_entry = ctk.CTkEntry(load_frame, placeholder_text="0.0")
        self.load_entry.pack(fill="x", pady=5)
        
        # Priority and delivery type
        options_frame = ctk.CTkFrame(route_section)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        priority_frame = ctk.CTkFrame(options_frame)
        priority_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(priority_frame, text="Priority:").pack(anchor="w")
        self.priority_var = tk.StringVar(value="Normal")
        priority_menu = ctk.CTkOptionMenu(priority_frame, values=["Low", "Normal", "High", "Urgent"],
                                        variable=self.priority_var)
        priority_menu.pack(fill="x", pady=5)
        
        delivery_frame = ctk.CTkFrame(options_frame)
        delivery_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(delivery_frame, text="Type:").pack(anchor="w")
        self.delivery_type_var = tk.StringVar(value="Standard")
        type_menu = ctk.CTkOptionMenu(delivery_frame, values=["Standard", "Express", "Fragile", "Bulk"],
                                    variable=self.delivery_type_var)
        type_menu.pack(fill="x", pady=5)
        
        # Action buttons
        buttons_frame = ctk.CTkFrame(route_section)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="➕ Add Stop", command=self.add_enhanced_stop,
                     height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(buttons_frame, text="🔄 Optimize Route", command=self.optimize_route,
                     height=40).pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Route list with enhanced view
        list_section = ctk.CTkFrame(left_panel)
        list_section.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(list_section, text="📋 Route Overview",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Create enhanced treeview for route display
        columns = ("Stop", "Address", "Priority", "Type", "Load", "Status")
        self.route_tree = ttk.Treeview(list_section, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.route_tree.heading(col, text=col)
            self.route_tree.column(col, width=80)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_section, orient="vertical", command=self.route_tree.yview)
        self.route_tree.configure(yscrollcommand=scrollbar.set)
        
        tree_frame = ctk.CTkFrame(list_section)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.route_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Route action buttons
        route_actions = ctk.CTkFrame(list_section)
        route_actions.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(route_actions, text="🗑 Remove Selected", command=self.remove_selected_stop,
                     width=120).pack(side="left", padx=5)
        ctk.CTkButton(route_actions, text="📤 Save Template", command=self.save_route_template,
                     width=120).pack(side="left", padx=5)
        ctk.CTkButton(route_actions, text="🚀 Start Route", command=self.start_enhanced_route,
                     width=120).pack(side="right", padx=5)
        
        # Right panel for map and analytics
        right_panel = ctk.CTkFrame(tab)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Map section
        map_section = ctk.CTkFrame(right_panel)
        map_section.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(map_section, text="🗺 Interactive Route Map",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Map placeholder (would be replaced with actual map widget)
        self.map_display = ctk.CTkTextbox(map_section, height=300)
        self.map_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.map_display.insert("1.0", "Interactive map will be displayed here.\nRoute visualization and real-time tracking.")
        
        # Route statistics
        stats_section = ctk.CTkFrame(right_panel)
        stats_section.pack(fill="x", pady=10)
        
        ctk.CTkLabel(stats_section, text="📊 Route Statistics",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        stats_grid = ctk.CTkFrame(stats_section)
        stats_grid.pack(fill="x", padx=10, pady=10)
        
        # Statistics display
        self.stats_labels = {}
        stats_items = [("Total Distance", "0 km"), ("Est. Time", "0 min"), 
                      ("Fuel Cost", "$0.00"), ("Load Capacity", "0%")]
        
        for i, (label, value) in enumerate(stats_items):
            frame = ctk.CTkFrame(stats_grid)
            frame.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
            
            ctk.CTkLabel(frame, text=label).pack()
            stat_label = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=18, weight="bold"))
            stat_label.pack()
            self.stats_labels[label] = stat_label
        
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)
    
    def create_delivery_tracking_tab(self):
        """Create delivery tracking tab"""
        tab = self.notebook.add("📦 Delivery Tracking")
        
        ctk.CTkLabel(tab, text="Real-time delivery tracking will be implemented here",
                    font=ctk.CTkFont(size=18)).pack(expand=True)
    
    def create_fleet_management_tab(self):
        """Create fleet management tab"""
        tab = self.notebook.add("🚛 Fleet Management")
        
        ctk.CTkLabel(tab, text="Fleet management features will be implemented here",
                    font=ctk.CTkFont(size=18)).pack(expand=True)
    
    def create_reports_tab(self):
        """Create reports and analytics tab"""
        tab = self.notebook.add("📈 Reports & Analytics")
        
        ctk.CTkLabel(tab, text="Advanced reporting and analytics will be implemented here",
                    font=ctk.CTkFont(size=18)).pack(expand=True)
    
    def on_van_selected(self, choice):
        """Handle vehicle selection"""
        for van in VAN_CAPACITY_DATA:
            if f"{van['make']} {van['model']}" in choice:
                self.total_capacity = van['capacity']
                efficiency = van['fuel_efficiency']
                self.capacity_info.configure(
                    text=f"Capacity: {van['capacity']}m³ | Fuel Efficiency: {efficiency}L/100km"
                )
                self.update_statistics()
                break
    
    def add_enhanced_stop(self):
        """Add a delivery stop with enhanced features"""
        address = self.address_entry.get().strip()
        time_str = self.time_entry.get().strip()
        load_str = self.load_entry.get().strip()
        priority = self.priority_var.get()
        delivery_type = self.delivery_type_var.get()
        
        if not address or not load_str:
            messagebox.showerror('Input Error', 'Address and load are required.')
            return
        
        try:
            load = float(load_str)
            est_time = int(time_str) if time_str else None
            
            if load <= 0:
                raise ValueError("Load must be positive")
            
            if self.used_capacity + load > self.total_capacity > 0:
                messagebox.showwarning('Capacity Warning', 
                                     f'Adding this load will exceed van capacity!\n'
                                     f'Current: {self.used_capacity:.1f}m³\n'
                                     f'Adding: {load:.1f}m³\n'
                                     f'Capacity: {self.total_capacity:.1f}m³')
                if not messagebox.askyesno('Continue?', 'Do you want to add this stop anyway?'):
                    return
            
            # Add to route tree immediately
            self.route_tree.insert("", 'end', values=(
                self.stop_counter, address[:30] + "..." if len(address) > 30 else address,
                priority, delivery_type, f"{load:.1f}m³", "Pending"
            ))
            
            # Geocode in background
            def geocode_address():
                try:
                    location = self.geolocator.geocode(address)
                    coords = f"{location.latitude:.5f},{location.longitude:.5f}" if location else "N/A"
                    weather = self.fetch_weather(location.latitude, location.longitude) if location else None
                    
                    # Calculate travel time if this isn't the first stop
                    if est_time is None and self.stops:
                        last_stop = self.stops[-1]
                        if last_stop['coords'] != 'N/A' and location:
                            lat, lon = map(float, last_stop['coords'].split(','))
                            travel_time = self.fetch_travel_time((lat, lon), (location.latitude, location.longitude))
                            est_time_final = max(int(travel_time), 5)  # Minimum 5 minutes
                        else:
                            est_time_final = 15  # Default
                    else:
                        est_time_final = est_time if est_time else 15
                        
                except Exception as e:
                    coords = "N/A"
                    weather = None
                    est_time_final = est_time if est_time else 15
                
                # Store stop data
                stop_data = {
                    'stop': self.stop_counter,
                    'address': address,
                    'priority': priority,
                    'delivery_type': delivery_type,
                    'est_time': est_time_final,
                    'load': load,
                    'coords': coords,
                    'weather': weather,
                    'completed': False,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.stops.append(stop_data)
                self.stop_counter += 1
                self.used_capacity += load
                
                # Update displays
                self.update_statistics()
                self.update_map_display()
                self.save_to_database(stop_data)
            
            threading.Thread(target=geocode_address, daemon=True).start()
            
            # Clear form
            self.address_entry.delete(0, 'end')
            self.time_entry.delete(0, 'end')
            self.load_entry.delete(0, 'end')
            
        except ValueError as e:
            messagebox.showerror('Input Error', f'Invalid input: {str(e)}')
    
    def optimize_route(self):
        """Optimize the delivery route using a simple algorithm"""
        if len(self.stops) < 2:
            messagebox.showinfo('Route Optimization', 'Need at least 2 stops to optimize route.')
            return
        
        # Simple optimization: sort by priority first, then by proximity
        def priority_value(stop):
            priority_map = {"Urgent": 4, "High": 3, "Normal": 2, "Low": 1}
            return priority_map.get(stop.get('priority', 'Normal'), 2)
        
        # Sort by priority (descending) and then by estimated time
        optimized_stops = sorted(self.stops, key=lambda x: (-priority_value(x), x.get('est_time', 0)))
        
        if optimized_stops != self.stops:
            self.stops = optimized_stops
            self.refresh_route_display()
            messagebox.showinfo('Route Optimized', 'Route has been optimized based on priority and travel time.')
        else:
            messagebox.showinfo('Route Optimization', 'Route is already optimized.')
    
    def refresh_route_display(self):
        """Refresh the route display tree"""
        # Clear current display
        for item in self.route_tree.get_children():
            self.route_tree.delete(item)
        
        # Repopulate with optimized route
        for i, stop in enumerate(self.stops, 1):
            self.route_tree.insert("", 'end', values=(
                i, 
                stop['address'][:30] + "..." if len(stop['address']) > 30 else stop['address'],
                stop.get('priority', 'Normal'),
                stop.get('delivery_type', 'Standard'),
                f"{stop['load']:.1f}m³",
                "Completed" if stop.get('completed', False) else "Pending"
            ))
    
    def remove_selected_stop(self):
        """Remove selected stop from route"""
        selected = self.route_tree.selection()
        if not selected:
            messagebox.showinfo('Selection', 'Please select a stop to remove.')
            return
        
        for item in selected:
            values = self.route_tree.item(item, 'values')
            stop_num = int(values[0]) - 1
            
            if stop_num < len(self.stops):
                removed_stop = self.stops.pop(stop_num)
                self.used_capacity -= removed_stop['load']
                self.route_tree.delete(item)
        
        self.update_statistics()
        self.refresh_route_display()
    
    def save_route_template(self):
        """Save current route as a template"""
        if not self.stops:
            messagebox.showinfo('Template', 'No stops to save as template.')
            return
        
        # Simple dialog for template name
        template_name = tk.simpledialog.askstring("Save Template", "Enter template name:")
        if template_name:
            template_data = {
                'name': template_name,
                'stops': self.stops.copy(),
                'created': datetime.now().isoformat()
            }
            self.route_templates.append(template_data)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO route_templates (name, description, route_data) VALUES (?, ?, ?)',
                         (template_name, f"Template with {len(self.stops)} stops", json.dumps(template_data)))
            conn.commit()
            conn.close()
            
            messagebox.showinfo('Template Saved', f'Route template "{template_name}" has been saved.')
    
    def start_enhanced_route(self):
        """Start the delivery route with enhanced tracking"""
        if not self.stops:
            messagebox.showinfo('No Route', 'Please add delivery stops first.')
            return
        
        # Show route confirmation dialog
        total_distance = sum(stop.get('est_time', 0) for stop in self.stops)
        total_load = sum(stop['load'] for stop in self.stops)
        
        message = f"""Route Summary:
        
🚚 Stops: {len(self.stops)}
⏱ Total Time: {total_distance} minutes
📦 Total Load: {total_load:.1f}m³
🚐 Vehicle Capacity: {self.total_capacity:.1f}m³

Ready to start delivery route?"""
        
        if messagebox.askyesno('Start Route', message):
            self.notebook.set("📦 Delivery Tracking")
            # Here you would implement real-time tracking
            messagebox.showinfo('Route Started', 'Delivery route has been started. Switch to Delivery Tracking tab for real-time updates.')
    
    def update_statistics(self):
        """Update route statistics display"""
        if hasattr(self, 'stats_labels'):
            total_distance = sum(stop.get('est_time', 0) for stop in self.stops) * 0.5  # Rough km estimate
            total_time = sum(stop.get('est_time', 0) for stop in self.stops)
            fuel_cost = total_distance * 0.15  # Rough fuel cost calculation
            capacity_used = (self.used_capacity / self.total_capacity * 100) if self.total_capacity > 0 else 0
            
            self.stats_labels["Total Distance"].configure(text=f"{total_distance:.1f} km")
            self.stats_labels["Est. Time"].configure(text=f"{total_time} min")
            self.stats_labels["Fuel Cost"].configure(text=f"${fuel_cost:.2f}")
            self.stats_labels["Load Capacity"].configure(text=f"{capacity_used:.1f}%")
    
    def update_map_display(self):
        """Update the map display with current route"""
        if hasattr(self, 'map_display'):
            map_text = "📍 Current Route:\n\n"
            for i, stop in enumerate(self.stops, 1):
                status = "✅" if stop.get('completed', False) else "⏳"
                priority_icon = {"Urgent": "🔴", "High": "🟠", "Normal": "🟡", "Low": "🟢"}.get(stop.get('priority', 'Normal'), "🟡")
                map_text += f"{status} {i}. {stop['address']} {priority_icon}\n"
                map_text += f"   Load: {stop['load']:.1f}m³ | Time: {stop.get('est_time', 0)} min\n\n"
            
            self.map_display.delete("1.0", 'end')
            self.map_display.insert("1.0", map_text)
    
    def save_to_database(self, stop_data):
        """Save stop data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO deliveries 
                         (address, load_size, delivery_time, coordinates, weather_temp) 
                         VALUES (?, ?, ?, ?, ?)''',
                      (stop_data['address'], stop_data['load'], stop_data.get('est_time'),
                       stop_data.get('coords'), stop_data.get('weather')))
        conn.commit()
        conn.close()
    
    def load_saved_data(self):
        """Load saved data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM route_templates ORDER BY created_at DESC LIMIT 5')
            templates = cursor.fetchall()
            conn.close()
            
            # Load recent templates for quick access
            for template in templates:
                try:
                    template_data = json.loads(template[3])
                    self.route_templates.append(template_data)
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error loading saved data: {e}")
    
    def fetch_weather(self, lat, lon):
        """Fetch weather data for coordinates"""
        cache_key = f"{lat},{lon}"
        if cache_key in self.weather_cache:
            return self.weather_cache[cache_key]
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            temp = data.get("current_weather", {}).get("temperature")
            if temp is not None:
                self.weather_cache[cache_key] = temp
            return temp
        except Exception:
            return None
    
    def fetch_travel_time(self, start, end):
        """Fetch travel time between two points"""
        # Try Google Maps API first if available
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            params = {
                "origin": f"{start[0]},{start[1]}",
                "destination": f"{end[0]},{end[1]}",
                "key": api_key,
            }
            try:
                resp = requests.get("https://maps.googleapis.com/maps/api/directions/json", 
                                  params=params, timeout=10)
                data = resp.json()
                if data.get("routes"):
                    duration = data["routes"][0]["legs"][0]["duration"]["value"] / 60
                    return duration
            except Exception:
                pass
        
        # Fallback to OSRM
        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=false"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return data["routes"][0]["duration"] / 60
        except Exception:
            return 15  # Default fallback time
    
    # Placeholder methods for advanced features
    def show_analytics(self):
        """Show advanced analytics dashboard"""
        analytics_window = ctk.CTkToplevel(self)
        analytics_window.title("📊 Advanced Analytics Dashboard")
        analytics_window.geometry("800x600")
        
        # Create analytics content
        main_frame = ctk.CTkFrame(analytics_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(main_frame, text="📊 Delivery Analytics Dashboard", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        # Statistics display
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.pack(fill="x", pady=10)
        
        # Calculate real statistics
        total_stops = len(self.stops)
        completed_stops = len([s for s in self.stops if s.get('completed', False)])
        total_load = sum(s.get('load', 0) for s in self.stops)
        avg_time = sum(s.get('est_time', 0) for s in self.stops) / len(self.stops) if self.stops else 0
        
        stats_data = [
            ("Total Deliveries", total_stops),
            ("Completed", completed_stops),
            ("Completion Rate", f"{(completed_stops/total_stops*100) if total_stops else 0:.1f}%"),
            ("Total Volume", f"{total_load:.1f}m³"),
            ("Avg. Time/Stop", f"{avg_time:.1f} min"),
            ("Efficiency Score", f"{(completed_stops/total_stops*100 + (total_load/self.total_capacity*100 if self.total_capacity else 0))/2 if total_stops else 0:.1f}%")
        ]
        
        # Display statistics in grid
        for i, (label, value) in enumerate(stats_data):
            stat_frame = ctk.CTkFrame(stats_frame)
            stat_frame.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            
            ctk.CTkLabel(stat_frame, text=label, font=ctk.CTkFont(size=12)).pack(pady=5)
            ctk.CTkLabel(stat_frame, text=str(value), font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Configure grid
        for i in range(3):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # Generate report button
        ctk.CTkButton(main_frame, text="📄 Generate Analytics Report", 
                     command=self.generate_analytics_report).pack(pady=20)
    
    def manage_templates(self):
        """Template management system"""
        template_window = ctk.CTkToplevel(self)
        template_window.title("📋 Route Templates")
        template_window.geometry("600x500")
        
        main_frame = ctk.CTkFrame(template_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="📋 Route Template Manager", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Template list
        template_frame = ctk.CTkFrame(main_frame)
        template_frame.pack(fill="both", expand=True, pady=10)
        
        # Create template listbox
        template_listbox = tk.Listbox(template_frame, height=15)
        template_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Populate with existing templates
        for template in self.route_templates:
            template_listbox.insert(tk.END, f"{template['name']} ({len(template.get('stops', []))} stops)")
        
        # Template actions
        actions_frame = ctk.CTkFrame(main_frame)
        actions_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(actions_frame, text="📥 Load Template", 
                     command=lambda: self.load_template(template_listbox)).pack(side="left", padx=5)
        ctk.CTkButton(actions_frame, text="🗑 Delete Template", 
                     command=lambda: self.delete_template(template_listbox)).pack(side="left", padx=5)
        ctk.CTkButton(actions_frame, text="📤 Export Template", 
                     command=lambda: self.export_template(template_listbox)).pack(side="right", padx=5)
    
    def export_data(self):
        """Advanced data export functionality"""
        export_window = ctk.CTkToplevel(self)
        export_window.title("📤 Export Data")
        export_window.geometry("500x400")
        
        main_frame = ctk.CTkFrame(export_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="📤 Data Export Options", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Export format selection
        format_frame = ctk.CTkFrame(main_frame)
        format_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(format_frame, text="Export Format:").pack(anchor="w", padx=10)
        
        self.export_format = tk.StringVar(value="CSV")
        formats = ["CSV", "JSON", "Daily Report", "Route Summary", "Delivery Confirmations"]
        
        for fmt in formats:
            ctk.CTkRadioButton(format_frame, text=fmt, variable=self.export_format, 
                              value=fmt).pack(anchor="w", padx=20, pady=2)
        
        # Export options
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        self.include_completed = tk.BooleanVar(value=True)
        self.include_pending = tk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(options_frame, text="Include Completed Deliveries", 
                       variable=self.include_completed).pack(anchor="w", padx=10, pady=5)
        ctk.CTkCheckBox(options_frame, text="Include Pending Deliveries", 
                       variable=self.include_pending).pack(anchor="w", padx=10, pady=5)
        
        # Export button
        ctk.CTkButton(main_frame, text="📤 Export Data", 
                     command=self.perform_export).pack(pady=20)
    
    def show_settings(self):
        """Advanced settings panel"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("⚙ Settings")
        settings_window.geometry("600x500")
        
        main_frame = ctk.CTkFrame(settings_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="⚙ CourierPro Settings", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Create tabview for settings categories
        settings_tabs = ctk.CTkTabview(main_frame)
        settings_tabs.pack(fill="both", expand=True)
        
        # General settings
        general_tab = settings_tabs.add("General")
        
        # Automation settings
        automation_tab = settings_tabs.add("Automation")
        
        # Notifications settings  
        notifications_tab = settings_tabs.add("Notifications")
        
        # General settings content
        ctk.CTkLabel(general_tab, text="🔧 General Preferences").pack(pady=10)
        
        # Default vehicle capacity
        capacity_frame = ctk.CTkFrame(general_tab)
        capacity_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(capacity_frame, text="Default Vehicle Capacity (m³):").pack(anchor="w")
        self.default_capacity = ctk.CTkEntry(capacity_frame, placeholder_text="15.0")
        self.default_capacity.pack(fill="x", pady=5)
        
        # Automation settings content
        ctk.CTkLabel(automation_tab, text="🤖 Automation Rules").pack(pady=10)
        
        self.auto_optimize = tk.BooleanVar(value=True)
        self.auto_backup = tk.BooleanVar(value=True)
        self.auto_reports = tk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(automation_tab, text="Auto-optimize routes when capacity > 80%", 
                       variable=self.auto_optimize).pack(anchor="w", padx=10, pady=5)
        ctk.CTkCheckBox(automation_tab, text="Auto-backup data daily", 
                       variable=self.auto_backup).pack(anchor="w", padx=10, pady=5)
        ctk.CTkCheckBox(automation_tab, text="Auto-generate daily reports", 
                       variable=self.auto_reports).pack(anchor="w", padx=10, pady=5)
        
        # Save settings button
        ctk.CTkButton(main_frame, text="💾 Save Settings", 
                     command=self.save_settings).pack(pady=10)
    
    def setup_default_automation_rules(self):
        """Setup default automation rules"""
        # Rule 1: Auto-optimize when capacity reaches 80%
        self.automation_engine.add_automation_rule(
            "capacity_optimizer",
            {"type": "capacity_threshold", "threshold_percent": 80},
            {"type": "optimize_route"}
        )
        
        # Rule 2: Generate daily backup at midnight
        self.automation_engine.add_automation_rule(
            "daily_backup",
            {"type": "time_based", "time": "00:00"},
            {"type": "backup_data"}
        )
        
        # Rule 3: Alert for urgent deliveries
        self.automation_engine.add_automation_rule(
            "urgent_alert",
            {"type": "priority_urgent", "min_urgent": 1},
            {"type": "send_notification", "message": "Urgent deliveries detected!"}
        )
    
    def start_automation_monitoring(self):
        """Start monitoring automation rules"""
        def monitor():
            while True:
                try:
                    # Convert stops to DeliveryStop objects for automation engine
                    delivery_stops = []
                    for stop in self.stops:
                        delivery_stop = DeliveryStop(
                            id=stop.get('stop', 0),
                            address=stop.get('address', ''),
                            priority=stop.get('priority', 'Normal'),
                            delivery_type=stop.get('delivery_type', 'Standard'),
                            load_size=stop.get('load', 0),
                            estimated_time=stop.get('est_time', 15),
                            status="completed" if stop.get('completed', False) else "pending"
                        )
                        delivery_stops.append(delivery_stop)
                    
                    # Check automation rules
                    self.automation_engine.check_and_execute_rules(delivery_stops)
                    
                    # Check for notifications
                    self.check_automation_notifications()
                    
                except Exception as e:
                    print(f"Automation monitoring error: {e}")
                
                # Sleep for 60 seconds before next check
                threading.Event().wait(60)
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def check_automation_notifications(self):
        """Check and display automation notifications"""
        unread_notifications = [n for n in self.automation_engine.notifications if not n.get('read', False)]
        
        if unread_notifications:
            # Show notification popup (in a real app, this would be more sophisticated)
            latest = unread_notifications[-1]
            # Mark as read
            latest['read'] = True
    
    def generate_analytics_report(self):
        """Generate comprehensive analytics report"""
        if not self.stops:
            messagebox.showinfo("No Data", "No delivery data available for report generation.")
            return
        
        # Convert stops to DeliveryStop objects
        delivery_stops = []
        for stop in self.stops:
            delivery_stop = DeliveryStop(
                id=stop.get('stop', 0),
                address=stop.get('address', ''),
                priority=stop.get('priority', 'Normal'),
                delivery_type=stop.get('delivery_type', 'Standard'),
                load_size=stop.get('load', 0),
                estimated_time=stop.get('est_time', 15),
                status="completed" if stop.get('completed', False) else "pending",
                created_at=datetime.now().isoformat()
            )
            delivery_stops.append(delivery_stop)
        
        # Generate comprehensive report
        report_content = self.content_engine.generate_daily_report(delivery_stops, "Current Driver")
        
        # Save to file
        filename = f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report_content)
        
        messagebox.showinfo("Report Generated", f"Analytics report saved to {filename}")
    
    def load_template(self, listbox):
        """Load selected template"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a template to load.")
            return
        
        template_index = selection[0]
        if template_index < len(self.route_templates):
            template = self.route_templates[template_index]
            
            # Clear current route
            self.clear_all()
            
            # Load template stops
            for stop_data in template.get('stops', []):
                self.stops.append(stop_data)
                self.route_tree.insert("", 'end', values=(
                    stop_data.get('stop', len(self.stops)),
                    stop_data.get('address', '')[:30],
                    stop_data.get('priority', 'Normal'),
                    stop_data.get('delivery_type', 'Standard'),
                    f"{stop_data.get('load', 0):.1f}m³",
                    "Pending"
                ))
                self.used_capacity += stop_data.get('load', 0)
            
            self.stop_counter = len(self.stops) + 1
            self.update_statistics()
            messagebox.showinfo("Template Loaded", f"Template '{template['name']}' loaded successfully.")
    
    def delete_template(self, listbox):
        """Delete selected template"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a template to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this template?"):
            template_index = selection[0]
            if template_index < len(self.route_templates):
                deleted_template = self.route_templates.pop(template_index)
                listbox.delete(template_index)
                messagebox.showinfo("Template Deleted", f"Template '{deleted_template['name']}' deleted.")
    
    def export_template(self, listbox):
        """Export selected template"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a template to export.")
            return
        
        template_index = selection[0]
        if template_index < len(self.route_templates):
            template = self.route_templates[template_index]
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Template"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(template, f, indent=2)
                messagebox.showinfo("Template Exported", f"Template exported to {filename}")
    
    def perform_export(self):
        """Perform data export based on selected options"""
        format_type = self.export_format.get()
        
        # Filter stops based on options
        filtered_stops = []
        for stop in self.stops:
            if stop.get('completed', False) and self.include_completed.get():
                filtered_stops.append(stop)
            elif not stop.get('completed', False) and self.include_pending.get():
                filtered_stops.append(stop)
        
        if not filtered_stops:
            messagebox.showinfo("No Data", "No data matches the selected criteria.")
            return
        
        # Convert to DeliveryStop objects
        delivery_stops = []
        for stop in filtered_stops:
            delivery_stop = DeliveryStop(
                id=stop.get('stop', 0),
                address=stop.get('address', ''),
                priority=stop.get('priority', 'Normal'),
                delivery_type=stop.get('delivery_type', 'Standard'),
                load_size=stop.get('load', 0),
                estimated_time=stop.get('est_time', 15),
                status="completed" if stop.get('completed', False) else "pending",
                customer_name=stop.get('customer_name'),
                special_instructions=stop.get('special_instructions'),
                created_at=datetime.now().isoformat()
            )
            delivery_stops.append(delivery_stop)
        
        try:
            if format_type == "CSV":
                filename = self.content_engine.export_to_csv(delivery_stops)
            elif format_type == "JSON": 
                filename = self.content_engine.export_to_json(delivery_stops)
            elif format_type == "Daily Report":
                report_content = self.content_engine.generate_daily_report(delivery_stops)
                filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(filename, 'w') as f:
                    f.write(report_content)
            elif format_type == "Route Summary":
                report_content = self.content_engine.generate_route_summary(delivery_stops)
                filename = f"route_summary_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(filename, 'w') as f:
                    f.write(report_content)
            elif format_type == "Delivery Confirmations":
                # Generate multiple delivery confirmations
                confirmations = []
                for stop in delivery_stops:
                    confirmation = self.content_engine.generate_delivery_confirmation(stop)
                    confirmations.append(f"=== DELIVERY {stop.id} ===\n{confirmation}\n\n")
                
                filename = f"delivery_confirmations_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(filename, 'w') as f:
                    f.write('\n'.join(confirmations))
            
            messagebox.showinfo("Export Complete", f"Data exported successfully to {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Error during export: {str(e)}")
    
    def save_settings(self):
        """Save application settings"""
        settings = {
            'default_capacity': self.default_capacity.get(),
            'auto_optimize': self.auto_optimize.get(),
            'auto_backup': self.auto_backup.get(),
            'auto_reports': self.auto_reports.get()
        }
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for key, value in settings.items():
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                          (key, json.dumps(value)))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")


if __name__ == '__main__':
    # Import simpledialog for template naming
    import tkinter.simpledialog
    tk.simpledialog = tkinter.simpledialog
    
    app = CourierProApp()
    app.mainloop()