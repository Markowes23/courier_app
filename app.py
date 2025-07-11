import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import threading
import math
import json
import os
import requests

# Built-in van capacity dataset previously stored in van_capacity.json
VAN_CAPACITY_DATA = [
    {"make": "Ford", "model": "Transit", "capacity": 11.0},
    {"make": "Mercedes", "model": "Sprinter", "capacity": 13.5},
    {"make": "Volkswagen", "model": "Crafter", "capacity": 14.0},
]

try:
    from tkintermapview import TkinterMapView
except ImportError:
    TkinterMapView = None

# Placeholder for mapping - Folium or similar could be integrated with a web widget
try:
    import folium
except ImportError:
    folium = None

class StopDropApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('STOP&DROP Courier App')
        self.geometry('1100x700')
        self.configure(bg='#1e1e2f')
        self.iconbitmap('')  # You can set your custom icon here
        self.stops = []
        self.progress = 0
        self.total_capacity = 0
        self.used_capacity = 0
        self.weather_cache = {}
        self.create_widgets()
        self.geolocator = Nominatim(user_agent="stopdrop_app")
        self.stop_counter = 1

    def create_widgets(self):
        # Top Frame for van & load
        van_frame = ttk.LabelFrame(self, text="Van Details")
        van_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nw')
        ttk.Label(van_frame, text='Make:').grid(row=0, column=0)
        self.van_make = ttk.Entry(van_frame, width=14)
        self.van_make.grid(row=0, column=1)
        ttk.Label(van_frame, text='Model:').grid(row=0, column=2)
        self.van_model = ttk.Entry(van_frame, width=14)
        self.van_model.grid(row=0, column=3)
        ttk.Label(van_frame, text='Capacity [m³]:').grid(row=0, column=4)
        self.van_capacity = ttk.Entry(van_frame, width=7)
        self.van_capacity.grid(row=0, column=5)
        ttk.Button(van_frame, text="Set Van", command=self.set_van).grid(row=0, column=6, padx=8)

        # Frame for adding stops
        stop_frame = ttk.LabelFrame(self, text="Add Stop")
        stop_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nw')
        ttk.Label(stop_frame, text='Address:').grid(row=0, column=0)
        self.address_entry = ttk.Entry(stop_frame, width=35)
        self.address_entry.grid(row=0, column=1)
        ttk.Label(stop_frame, text='Est. Time [min]:').grid(row=0, column=2)
        self.time_entry = ttk.Entry(stop_frame, width=7)
        self.time_entry.grid(row=0, column=3)
        ttk.Label(stop_frame, text='Load [m³]:').grid(row=0, column=4)
        self.load_entry = ttk.Entry(stop_frame, width=7)
        self.load_entry.grid(row=0, column=5)
        ttk.Button(stop_frame, text="Add", command=self.add_stop).grid(row=0, column=6, padx=8)

        # Frame for route & stop list
        list_frame = ttk.LabelFrame(self, text="Route / Stops")
        list_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        self.tree = ttk.Treeview(list_frame, columns=("#1", "#2", "#3", "#4", "#5"), show="headings", height=12)
        self.tree.heading("#1", text="Stop")
        self.tree.heading("#2", text="Address")
        self.tree.heading("#3", text="Est. Time")
        self.tree.heading("#4", text="Load [m³]")
        self.tree.heading("#5", text="Coords")
        self.tree.grid(row=0, column=0)
        ttk.Button(list_frame, text="Remove Selected", command=self.remove_selected).grid(row=1, column=0, pady=4)
        ttk.Button(list_frame, text="Clear All", command=self.clear_all).grid(row=2, column=0)

        # Progress bar & info
        progress_frame = ttk.LabelFrame(self, text="Progress")
        progress_frame.grid(row=3, column=0, padx=10, pady=10, sticky='nw')
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, maximum=100, variable=self.progress_var, length=370)
        self.progress_bar.grid(row=0, column=0, padx=8, pady=4)
        self.progress_label = ttk.Label(progress_frame, text='Progress: 0%')
        self.progress_label.grid(row=1, column=0)
        ttk.Button(progress_frame, text="Start Route", command=self.start_route).grid(row=2, column=0, pady=4)

        # Map section placeholder (would be Folium + webview in real app)
        map_frame = ttk.LabelFrame(self, text="Map (Feature Demo)")
        map_frame.grid(row=0, column=1, rowspan=4, padx=16, pady=10)
        self.map_label = tk.Label(map_frame, text="[Map Preview]\n(This can be replaced with a live Folium widget or webview)", width=48, height=32, bg="#222238", fg="#cccccc", anchor='nw', justify='left', font=('Consolas', 10))
        self.map_label.pack()

    def set_van(self):
        make = self.van_make.get().strip()
        model = self.van_model.get().strip()
        cap_str = self.van_capacity.get().strip()
        capacity = None
        if cap_str:
            try:
                capacity = float(cap_str)
            except ValueError:
                capacity = None
        if capacity is None:
            capacity = self.fetch_van_capacity(make, model)
            if capacity:
                self.van_capacity.delete(0, tk.END)
                self.van_capacity.insert(0, str(capacity))
        if not capacity or capacity <= 0:
            messagebox.showerror('Input error', 'Please enter a valid capacity or ensure make/model are correct.')
            return
        self.total_capacity = capacity
        messagebox.showinfo('Van set', f"Van set: {make} {model} ({capacity} m³)")

    def add_stop(self):
        address = self.address_entry.get().strip()
        time_str = self.time_entry.get().strip()
        load_str = self.load_entry.get().strip()
        if not address or not load_str:
            messagebox.showerror('Input error', 'Address and load are required.')
            return
        try:
            est_time = int(time_str) if time_str else None
            load = float(load_str)
            if load <= 0 or (est_time is not None and est_time <= 0):
                raise ValueError
            if self.used_capacity + load > self.total_capacity > 0:
                messagebox.showwarning('Capacity full', 'Van capacity will be exceeded!')
                return
            # Geocode address (can be slow, so run in thread)
            def fetch_coords():
                try:
                    location = self.geolocator.geocode(address)
                    if not location:
                        raise Exception('Address not found')
                    coords = f"{location.latitude:.5f},{location.longitude:.5f}"
                    if est_time is None and self.stops:
                        last = self.stops[-1]
                        if last['coords'] != 'N/A':
                            lat, lon = map(float, last['coords'].split(','))
                            est = self.fetch_travel_time((lat, lon), (location.latitude, location.longitude))
                            est_time_local = int(max(est, 1))
                        else:
                            est_time_local = 0
                        self.time_entry.delete(0, tk.END)
                        self.time_entry.insert(0, str(est_time_local))
                    else:
                        est_time_local = est_time if est_time is not None else 0
                    weather = self.fetch_weather(location.latitude, location.longitude)
                except Exception as e:
                    coords = "N/A"
                    est_time_local = est_time if est_time is not None else 0
                    weather = None
                self.tree.insert("", 'end', values=(self.stop_counter, address, f"{est_time_local} min", f"{load} m³", coords))
                self.stops.append({'stop': self.stop_counter, 'address': address, 'est_time': est_time_local, 'load': load, 'coords': coords, 'weather': weather, 'completed': False})
                self.stop_counter += 1
                self.used_capacity += load
                self.update_progress()
            threading.Thread(target=fetch_coords).start()
        except ValueError:
            messagebox.showerror('Input error', 'Estimated time and Load must be positive numbers.')

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for item in selected:
            idx = int(self.tree.item(item, 'values')[0]) - 1
            stop = self.stops[idx]
            if stop['completed']:
                continue
            self.used_capacity -= stop['load']
            self.stops[idx]['load'] = 0
            self.tree.delete(item)
        self.update_progress()

    def clear_all(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.stops = []
        self.stop_counter = 1
        self.used_capacity = 0
        self.update_progress()

    def update_progress(self):
        total = len(self.stops)
        done = sum(1 for s in self.stops if s['completed'])
        pct = 100 * done / total if total > 0 else 0
        self.progress_var.set(pct)
        self.progress_label.config(text=f'Progress: {pct:.1f}%')
        # Map update - in real app, update map widget
        self.map_label.config(text=f"Stops completed: {done}/{total}\nProgress: {pct:.1f}%\n(Van Load: {self.used_capacity:.2f}/{self.total_capacity:.2f} m³)")

    def fetch_van_capacity(self, make, model):
        for entry in VAN_CAPACITY_DATA:
            if entry["make"].lower() == make.lower() and entry["model"].lower() == model.lower():
                return entry["capacity"]
        return None

    def fetch_weather(self, lat, lon):
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
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            params = {
                "origin": f"{start[0]},{start[1]}",
                "destination": f"{end[0]},{end[1]}",
                "key": api_key,
            }
            try:
                resp = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=params, timeout=10)
                data = resp.json()
                if data.get("routes"):
                    dur = data["routes"][0]["legs"][0]["duration"]["value"] / 60
                    return dur
            except Exception:
                pass
        # fallback to OSRM
        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=false"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return data["routes"][0]["duration"] / 60
        except Exception:
            return 0

class MapWindow(tk.Toplevel):
    def __init__(self, master, stops):
        super().__init__(master)
        self.title("Route Map")
        self.geometry("800x600")
        if TkinterMapView is None:
            ttk.Label(self, text="tkintermapview not installed").pack(padx=20, pady=20)
            return
        self.map = TkinterMapView(self, width=780, height=560)
        self.map.pack(padx=10, pady=10)
        for stop in stops:
            if stop['coords'] != 'N/A':
                lat, lon = map(float, stop['coords'].split(','))
                text = f"{stop['stop']}: {stop['address']}"
                if stop.get('weather') is not None:
                    text += f"\nTemp: {stop['weather']}°C"
                self.map.set_marker(lat, lon, text=text)
        if stops and stops[0]['coords'] != 'N/A':
            lat, lon = map(float, stops[0]['coords'].split(','))
            self.map.set_position(lat, lon)

    def start_route(self):
        if not self.stops:
            messagebox.showinfo('No stops', 'Add at least one stop to start route.')
            return
        MapWindow(self, self.stops)

        def schedule_alerts():
            now = datetime.now()
            elapsed = 0
            for stop in self.stops:
                elapsed += stop['est_time']
                alert_time = now + timedelta(minutes=elapsed - 5)
                delay = (alert_time - datetime.now()).total_seconds()
                if delay > 0:
                    threading.Timer(delay, lambda s=stop: messagebox.showinfo('Reminder', f"Delivery for {s['address']} soon" )).start()

        schedule_alerts()

        def route_task():
            for idx, stop in enumerate(self.stops):
                # Simulate user confirming arrival and drop
                if stop['completed']:
                    continue
                answer = messagebox.askyesno('Confirm', f"Arrived at stop {stop['stop']}? ({stop['address']})")
                if not answer:
                    break
                self.stops[idx]['completed'] = True
                self.update_progress()
                # Simulate time spent
                mins = stop['est_time']
                self.after(100, lambda: None)
                for _ in range(mins):
                    self.update()
                    self.after(10)  # Simulated fast-forward
            messagebox.showinfo('Route completed', 'You have completed all stops!')
            self.update_progress()
        threading.Thread(target=route_task).start()

if __name__ == '__main__':
    app = StopDropApp()
    app.mainloop()
