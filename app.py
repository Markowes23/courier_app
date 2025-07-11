import tkinter as tk
from tkinter import ttk, messagebox
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
import math
import random

# --- LION LOGO SVG as PNG for Tkinter ---
import io
import base64

lion_png_base64 = '''
iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAYAAABf2VzdAAABuElEQVR4nO2XPU7DMBCGH0E0LZ6CY2T0A1AqFpNYRxZr1HLQxwKxw5I9zOsYk4PCEp4w8A3/XkOl+G2b9/AXKZeQAAxCAIAQAkAMlR4Q2Bn4EpMPkv0QACBfpm8N4KhQhVgs93OlFFGkEyXph2BvHACIFAXDFaCmTyEM5muc5lhwZhHcwU+ESCoVTi0ZplIlUtlPWW4VUQBgtGrqDtbnhPtU3Q74jUt6lsvg0+phcR9v6DVdVgyU6TPgWX9uR8G0dExRe+rW0h24CJ3oHlsfP6gTlgHwAP51PvVZhtr3E2EjgLRDk+6zF16wUn/5AuSMIXbJbUAQ1bw+v4mJUPwqksL3WkmkLMqkiWwBtao41qqLMqEOonPoSb7w7MKpD0qB3lTbpSCLLaAK3WAsJe5pjEyjA0Isp1I1HiE4jKBrpt2tkFNAhQ2ZDnIUUNsUpZmQ7lDTLKQ2ZBv6QCzB9snNvm7V0KZB5V9VYFQAA1QQ9GmQCgACgVAGp8T4F8g7vY6U1QAAAABJRU5ErkJggg==
'''

lion_img = Image.open(io.BytesIO(base64.b64decode(lion_png_base64.strip())))
lion_img = lion_img.resize((48, 48))
lion_img_tk = ImageTk.PhotoImage(lion_img)

BOLD_ORANGE = "#FF6600"

class JobManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Job Manager - Big Lion")
        self.geometry("1100x700")
        self.configure(bg="#fff8f0")
        self.jobs = [
            {"address": "320 Cedar St", "time": "09:00", "duration": 60, "coords": (52.2297, 21.0122)},
            {"address": "101 Maple Ave", "time": "11:00", "duration": 10, "coords": (52.2307, 21.0022)},
            {"address": "550 Walnut St", "time": "12:00", "duration": 60, "coords": (52.2327, 21.0082)},
        ]
        self.init_ui()
        self.refresh_jobs()
        self.update_map()

    def init_ui(self):
        # Header
        header = tk.Frame(self, bg="#fff8f0")
        header.pack(side=tk.TOP, fill=tk.X, pady=10, padx=12)
        tk.Label(header, image=lion_img_tk, bg="#fff8f0").pack(side=tk.LEFT)
        tk.Label(header, text="JOB MANAGER", fg=BOLD_ORANGE, bg="#fff8f0",
                 font=("Segoe UI", 24, "bold"), padx=10).pack(side=tk.LEFT)
        tk.Label(header, text="Daily Schedule", fg="#bc5c00", bg="#fff8f0",
                 font=("Segoe UI", 16, "bold")).pack(side=tk.RIGHT, padx=24)

        # Main
        main = tk.Frame(self, bg="#fff8f0")
        main.pack(expand=True, fill=tk.BOTH, padx=16, pady=8)
        # Left panel: job list and form
        left = tk.Frame(main, bg="#fff8f0")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8)
        # Job List
        tk.Label(left, text="Job List", fg=BOLD_ORANGE, bg="#fff8f0",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 10))
        self.jobs_frame = tk.Frame(left, bg="#fff8f0")
        self.jobs_frame.pack(fill=tk.BOTH, expand=True)
        # Add job form
        form = tk.Frame(left, bg="#fff8f0")
        form.pack(pady=10, fill=tk.X)
        self.addr_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.dur_var = tk.IntVar(value=10)
        tk.Entry(form, textvariable=self.addr_var, width=26, font=("Segoe UI", 12), relief="ridge", bd=2).pack(pady=2)
        tk.Entry(form, textvariable=self.time_var, width=26, font=("Segoe UI", 12), relief="ridge", bd=2).pack(pady=2)
        tk.Entry(form, textvariable=self.dur_var, width=26, font=("Segoe UI", 12), relief="ridge", bd=2).pack(pady=2)
        ttk.Button(form, text="+ Add Job", style="Bold.TButton", command=self.add_job).pack(pady=6)
        # Map panel
        self.map_widget = TkinterMapView(main, width=700, height=480, corner_radius=16)
        self.map_widget.pack(side=tk.LEFT, padx=16, pady=8)
        self.map_widget.set_position(52.23, 21.01)
        self.map_widget.set_zoom(14)
        # Summary
        summary = tk.Frame(self, bg="#fff8f0")
        summary.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=14)
        self.jobs_count_var = tk.StringVar()
        self.travel_time_var = tk.StringVar()
        self.work_time_var = tk.StringVar()
        tk.Label(summary, textvariable=self.jobs_count_var, font=("Segoe UI", 14, "bold"),
                 fg=BOLD_ORANGE, bg="#fff8f0").pack(side=tk.LEFT, padx=10)
        tk.Label(summary, textvariable=self.travel_time_var, font=("Segoe UI", 14, "bold"),
                 fg="#cc5700", bg="#fff8f0").pack(side=tk.LEFT, padx=10)
        tk.Label(summary, textvariable=self.work_time_var, font=("Segoe UI", 14, "bold"),
                 fg="#cc5700", bg="#fff8f0").pack(side=tk.LEFT, padx=10)
        ttk.Button(summary, text="Optimize Route", style="Big.TButton", command=self.optimize_route).pack(side=tk.RIGHT, padx=24)

        # Style
        style = ttk.Style(self)
        style.configure("Bold.TButton", font=("Segoe UI", 11, "bold"), background=BOLD_ORANGE, foreground="#fff")
        style.configure("Big.TButton", font=("Segoe UI", 14, "bold"), background=BOLD_ORANGE, foreground="#fff")

    def refresh_jobs(self):
        for widget in self.jobs_frame.winfo_children():
            widget.destroy()
        for idx, job in enumerate(self.jobs):
            f = tk.Frame(self.jobs_frame, bg="#fff8f0")
            f.pack(fill=tk.X, pady=3)
            tk.Label(f, text=chr(65+idx), bg=BOLD_ORANGE, fg="#fff",
                     font=("Segoe UI", 13, "bold"), width=3, height=1).pack(side=tk.LEFT, padx=3)
            info = f"{job['address']} | {job['time']} | {job['duration']} min"
            tk.Label(f, text=info, font=("Segoe UI", 11), bg="#fff8f0", anchor="w").pack(side=tk.LEFT)
            tk.Button(f, text="❌", font=("Arial", 10, "bold"),
                      fg="#a44", bg="#fff8f0", bd=0,
                      command=lambda i=idx: self.delete_job(i)).pack(side=tk.RIGHT, padx=4)

        # Update summary
        self.jobs_count_var.set(f"Total Jobs: {len(self.jobs)}")
        self.travel_time_var.set(f"  |  Travel: {self.calc_total_travel()} min")
        self.work_time_var.set(f"  |  Work: {sum(j['duration'] for j in self.jobs)} min")

    def haversine(self, p1, p2):
        # Distance in km between two (lat, lon)
        R = 6371
        lat1, lon1 = p1
        lat2, lon2 = p2
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def calc_total_travel(self):
        # Fake "travel" estimate
        km = 0
        for i in range(1, len(self.jobs)):
            km += self.haversine(self.jobs[i-1]["coords"], self.jobs[i]["coords"])
        mins = km / 40 * 60  # 40 km/h
        return int(round(mins))

    def update_map(self):
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        for idx, job in enumerate(self.jobs):
            marker = self.map_widget.set_marker(
                job["coords"][0], job["coords"][1],
                text=f"{chr(65+idx)}. {job['address']}",
                marker_color_circle=BOLD_ORANGE,
                marker_color_outside=BOLD_ORANGE)
        if len(self.jobs) >= 2:
            self.map_widget.set_path([j["coords"] for j in self.jobs])

    def add_job(self):
        addr = self.addr_var.get().strip()
        time = self.time_var.get().strip()
        dur = self.dur_var.get()
        if not addr or not time:
            messagebox.showerror("Missing info", "Address and time required!")
            return
        # Fake random coords for demo, like before
        last = self.jobs[-1]["coords"]
        coords = (last[0]+random.uniform(-0.005, 0.005), last[1]+random.uniform(-0.01, 0.01))
        self.jobs.append({"address": addr, "time": time, "duration": dur, "coords": coords})
        self.addr_var.set("")
        self.time_var.set("")
        self.dur_var.set(10)
        self.refresh_jobs()
        self.update_map()

    def delete_job(self, idx):
        self.jobs.pop(idx)
        self.refresh_jobs()
        self.update_map()

    def optimize_route(self):
        # Simple: sort by job time (for demo)
        self.jobs.sort(key=lambda j: j["time"])
        self.refresh_jobs()
        self.update_map()

if __name__ == "__main__":
    app = JobManagerApp()
    app.mainloop()
