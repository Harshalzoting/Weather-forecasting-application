import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import time
from PIL import Image, ImageTk
import io
import base64

class AdvancedWeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Weather Forecast Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a2e')
        
        # Weather data storage
        self.current_weather = {}
        self.forecast_data = []
        self.hourly_data = []
        self.animation_running = False
        
        # API key - replace with your OpenWeatherMap API key
        self.api_key = ""  # Get from openweathermap.org
        
        self.setup_ui()
        self.setup_charts()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Search and current weather
        top_frame = tk.Frame(main_frame, bg='#16213e', relief=tk.RAISED, bd=2)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search section
        search_frame = tk.Frame(top_frame, bg='#16213e')
        search_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(search_frame, text="Enter City:", font=('Arial', 12, 'bold'), 
                fg='white', bg='#16213e').pack(side=tk.LEFT, padx=(0, 10))
        
        self.city_entry = tk.Entry(search_frame, font=('Arial', 12), width=25, 
                                  bg='#2a2a3e', fg='white', insertbackground='white')
        self.city_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.city_entry.bind('<Return>', lambda e: self.get_weather())
        
        search_btn = tk.Button(search_frame, text="Get Weather", command=self.get_weather,
                              bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'),
                              cursor='hand2', relief=tk.FLAT, padx=20)
        search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Auto-refresh toggle
        self.auto_refresh = tk.BooleanVar()
        refresh_check = tk.Checkbutton(search_frame, text="Auto Refresh (30s)", 
                                     variable=self.auto_refresh, font=('Arial', 10),
                                     fg='white', bg='#16213e', selectcolor='#2a2a3e',
                                     command=self.toggle_auto_refresh)
        refresh_check.pack(side=tk.LEFT, padx=(10, 0))
        
        # Current weather display
        self.current_frame = tk.Frame(top_frame, bg='#16213e')
        self.current_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # Main content area
        content_frame = tk.Frame(main_frame, bg='#1a1a2e')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Charts
        left_panel = tk.Frame(content_frame, bg='#16213e', relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right panel - Forecast cards
        right_panel = tk.Frame(content_frame, bg='#16213e', relief=tk.RAISED, bd=2, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # Chart notebook
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Forecast scroll area
        forecast_label = tk.Label(right_panel, text="5-Day Forecast", 
                                font=('Arial', 14, 'bold'), fg='white', bg='#16213e')
        forecast_label.pack(pady=(10, 0))
        
        # Scrollable forecast frame
        forecast_canvas = tk.Canvas(right_panel, bg='#16213e', highlightthickness=0)
        forecast_scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=forecast_canvas.yview)
        self.forecast_scroll_frame = tk.Frame(forecast_canvas, bg='#16213e')
        
        self.forecast_scroll_frame.bind(
            "<Configure>",
            lambda e: forecast_canvas.configure(scrollregion=forecast_canvas.bbox("all"))
        )
        
        forecast_canvas.create_window((0, 0), window=self.forecast_scroll_frame, anchor="nw")
        forecast_canvas.configure(yscrollcommand=forecast_scrollbar.set)
        
        forecast_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        forecast_scrollbar.pack(side="right", fill="y", pady=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Enter a city name to get weather data")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                            relief=tk.SUNKEN, anchor=tk.W, bg='#2a2a3e', fg='white')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
    def setup_charts(self):
        # Temperature chart
        self.temp_frame = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.temp_frame, text="Temperature Trends")
        
        self.temp_fig, self.temp_ax = plt.subplots(figsize=(10, 4), facecolor='#1a1a2e')
        self.temp_ax.set_facecolor('#2a2a3e')
        self.temp_canvas = FigureCanvasTkAgg(self.temp_fig, self.temp_frame)
        self.temp_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Humidity & Pressure chart
        self.humidity_frame = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.humidity_frame, text="Humidity & Pressure")
        
        self.humidity_fig, (self.humidity_ax, self.pressure_ax) = plt.subplots(2, 1, figsize=(10, 4), facecolor='#1a1a2e')
        self.humidity_ax.set_facecolor('#2a2a3e')
        self.pressure_ax.set_facecolor('#2a2a3e')
        self.humidity_canvas = FigureCanvasTkAgg(self.humidity_fig, self.humidity_frame)
        self.humidity_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Wind chart
        self.wind_frame = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.wind_frame, text="Wind Analysis")
        
        self.wind_fig, self.wind_ax = plt.subplots(figsize=(10, 4), facecolor='#1a1a2e', subplot_kw=dict(projection='polar'))
        self.wind_ax.set_facecolor('#2a2a3e')
        self.wind_canvas = FigureCanvasTkAgg(self.wind_fig, self.wind_frame)
        self.wind_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Real-time data simulation
        self.realtime_frame = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.realtime_frame, text="Live Data")
        
        self.realtime_fig, self.realtime_ax = plt.subplots(figsize=(10, 4), facecolor='#1a1a2e')
        self.realtime_ax.set_facecolor('#2a2a3e')
        self.realtime_canvas = FigureCanvasTkAgg(self.realtime_fig, self.realtime_frame)
        self.realtime_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize real-time data
        self.realtime_data = {'time': [], 'temp': [], 'humidity': []}
        self.start_realtime_animation()
        
    def get_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name")
            return
            
        self.status_var.set(f"Fetching weather data for {city}...")
        
        # Run in separate thread to prevent UI freezing
        threading.Thread(target=self.fetch_weather_data, args=(city,), daemon=True).start()
        
    def fetch_weather_data(self, city):
        try:
            # Current weather
            current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
            current_response = requests.get(current_url, timeout=10)
            
            if current_response.status_code == 200:
                self.current_weather = current_response.json()
                
                # 5-day forecast
                forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.api_key}&units=metric"
                forecast_response = requests.get(forecast_url, timeout=10)
                
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    self.forecast_data = forecast_data['list']
                    
                    # Update UI in main thread
                    self.root.after(0, self.update_weather_display)
                    self.root.after(0, lambda: self.status_var.set(f"Weather data updated for {city}"))
                else:
                    self.root.after(0, lambda: self.status_var.set("Error fetching forecast data"))
            else:
                error_msg = f"City not found: {city}"
                if current_response.status_code == 401:
                    error_msg = "API key invalid or missing"
                self.root.after(0, lambda: self.status_var.set(error_msg))
                
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: self.status_var.set(f"Network error: {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            
    def update_weather_display(self):
        # Clear current weather display
        for widget in self.current_frame.winfo_children():
            widget.destroy()
            
        if not self.current_weather:
            return
            
        # Current weather info
        city_name = self.current_weather['name']
        country = self.current_weather['sys']['country']
        temp = self.current_weather['main']['temp']
        feels_like = self.current_weather['main']['feels_like']
        humidity = self.current_weather['main']['humidity']
        pressure = self.current_weather['main']['pressure']
        description = self.current_weather['weather'][0]['description'].title()
        wind_speed = self.current_weather['wind']['speed']
        wind_dir = self.current_weather['wind'].get('deg', 0)
        
        # Current weather layout
        current_info = tk.Frame(self.current_frame, bg='#16213e')
        current_info.pack(fill=tk.X)
        
        # Left side - main info
        left_info = tk.Frame(current_info, bg='#16213e')
        left_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        city_label = tk.Label(left_info, text=f"{city_name}, {country}", 
                            font=('Arial', 18, 'bold'), fg='#4CAF50', bg='#16213e')
        city_label.pack(anchor=tk.W)
        
        temp_label = tk.Label(left_info, text=f"{temp:.1f}°C", 
                            font=('Arial', 32, 'bold'), fg='white', bg='#16213e')
        temp_label.pack(anchor=tk.W)
        
        desc_label = tk.Label(left_info, text=description, 
                            font=('Arial', 14), fg='#cccccc', bg='#16213e')
        desc_label.pack(anchor=tk.W)
        
        feels_label = tk.Label(left_info, text=f"Feels like {feels_like:.1f}°C", 
                             font=('Arial', 12), fg='#cccccc', bg='#16213e')
        feels_label.pack(anchor=tk.W)
        
        # Right side - additional info
        right_info = tk.Frame(current_info, bg='#16213e')
        right_info.pack(side=tk.RIGHT, padx=20)
        
        details = [
            ("Humidity", f"{humidity}%"),
            ("Pressure", f"{pressure} hPa"),
            ("Wind Speed", f"{wind_speed} m/s"),
            ("Wind Direction", f"{wind_dir}°")
        ]
        
        for label, value in details:
            detail_frame = tk.Frame(right_info, bg='#16213e')
            detail_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(detail_frame, text=f"{label}:", font=('Arial', 10), 
                   fg='#cccccc', bg='#16213e').pack(side=tk.LEFT)
            tk.Label(detail_frame, text=value, font=('Arial', 10, 'bold'), 
                   fg='white', bg='#16213e').pack(side=tk.RIGHT)
        
        # Update charts
        self.update_charts()
        self.update_forecast_cards()
        
    def update_charts(self):
        if not self.forecast_data:
            return
            
        # Prepare data
        times = []
        temps = []
        humidity_vals = []
        pressure_vals = []
        wind_speeds = []
        wind_dirs = []
        
        for item in self.forecast_data[:24]:  # 24 hours of data
            times.append(datetime.fromtimestamp(item['dt']))
            temps.append(item['main']['temp'])
            humidity_vals.append(item['main']['humidity'])
            pressure_vals.append(item['main']['pressure'])
            wind_speeds.append(item['wind']['speed'])
            wind_dirs.append(item['wind'].get('deg', 0))
        
        # Temperature chart
        self.temp_ax.clear()
        self.temp_ax.plot(times, temps, color='#FF6B6B', linewidth=2, marker='o', markersize=4)
        self.temp_ax.set_title('Temperature Trend (24h)', color='white', fontsize=14, fontweight='bold')
        self.temp_ax.set_ylabel('Temperature (°C)', color='white')
        self.temp_ax.tick_params(colors='white')
        self.temp_ax.grid(True, alpha=0.3, color='white')
        self.temp_fig.autofmt_xdate()
        self.temp_canvas.draw()
        
        # Humidity chart
        self.humidity_ax.clear()
        self.humidity_ax.plot(times, humidity_vals, color='#4ECDC4', linewidth=2, marker='s', markersize=4)
        self.humidity_ax.set_title('Humidity Levels', color='white', fontsize=12, fontweight='bold')
        self.humidity_ax.set_ylabel('Humidity (%)', color='white')
        self.humidity_ax.tick_params(colors='white')
        self.humidity_ax.grid(True, alpha=0.3, color='white')
        
        # Pressure chart
        self.pressure_ax.clear()
        self.pressure_ax.plot(times, pressure_vals, color='#45B7D1', linewidth=2, marker='^', markersize=4)
        self.pressure_ax.set_title('Atmospheric Pressure', color='white', fontsize=12, fontweight='bold')
        self.pressure_ax.set_ylabel('Pressure (hPa)', color='white')
        self.pressure_ax.tick_params(colors='white')
        self.pressure_ax.grid(True, alpha=0.3, color='white')
        
        self.humidity_fig.tight_layout()
        self.humidity_canvas.draw()
        
        # Wind chart (polar)
        self.wind_ax.clear()
        wind_dirs_rad = np.radians(wind_dirs)
        self.wind_ax.scatter(wind_dirs_rad, wind_speeds, c=wind_speeds, cmap='viridis', s=50, alpha=0.7)
        self.wind_ax.set_title('Wind Pattern (24h)', color='white', fontsize=14, fontweight='bold', pad=20)
        self.wind_ax.set_theta_zero_location('N')
        self.wind_ax.set_theta_direction(-1)
        self.wind_ax.tick_params(colors='white')
        self.wind_canvas.draw()
        
    def update_forecast_cards(self):
        # Clear existing forecast cards
        for widget in self.forecast_scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.forecast_data:
            return
        
        # Group forecast by day
        daily_forecasts = {}
        for item in self.forecast_data:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            if date not in daily_forecasts:
                daily_forecasts[date] = []
            daily_forecasts[date].append(item)
        
        # Create forecast cards
        for i, (date, day_data) in enumerate(list(daily_forecasts.items())[:5]):
            card_frame = tk.Frame(self.forecast_scroll_frame, bg='#2a2a3e', relief=tk.RAISED, bd=2)
            card_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Date
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_label = tk.Label(card_frame, text=date_obj.strftime('%A, %b %d'), 
                                font=('Arial', 12, 'bold'), fg='#4CAF50', bg='#2a2a3e')
            date_label.pack(pady=(10, 5))
            
            # Get day summary (use noon data if available, otherwise first entry)
            noon_data = None
            for item in day_data:
                hour = datetime.fromtimestamp(item['dt']).hour
                if hour == 12:
                    noon_data = item
                    break
            
            if not noon_data:
                noon_data = day_data[0]
            
            # Temperature range
            max_temp = max(item['main']['temp_max'] for item in day_data)
            min_temp = min(item['main']['temp_min'] for item in day_data)
            
            temp_frame = tk.Frame(card_frame, bg='#2a2a3e')
            temp_frame.pack(fill=tk.X, padx=10)
            
            tk.Label(temp_frame, text=f"High: {max_temp:.1f}°C", 
                   font=('Arial', 10), fg='#FF6B6B', bg='#2a2a3e').pack(side=tk.LEFT)
            tk.Label(temp_frame, text=f"Low: {min_temp:.1f}°C", 
                   font=('Arial', 10), fg='#4ECDC4', bg='#2a2a3e').pack(side=tk.RIGHT)
            
            # Weather description
            desc = noon_data['weather'][0]['description'].title()
            tk.Label(card_frame, text=desc, font=('Arial', 10), 
                   fg='#cccccc', bg='#2a2a3e').pack(pady=5)
            
            # Additional details
            details_frame = tk.Frame(card_frame, bg='#2a2a3e')
            details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            humidity = noon_data['main']['humidity']
            wind = noon_data['wind']['speed']
            
            tk.Label(details_frame, text=f"💧 {humidity}%", font=('Arial', 9), 
                   fg='#cccccc', bg='#2a2a3e').pack(side=tk.LEFT)
            tk.Label(details_frame, text=f"💨 {wind:.1f} m/s", font=('Arial', 9), 
                   fg='#cccccc', bg='#2a2a3e').pack(side=tk.RIGHT)
    
    def start_realtime_animation(self):
        """Start animated real-time data simulation"""
        self.animation_running = True
        
        def update_realtime_data():
            if not self.animation_running:
                return
                
            current_time = datetime.now()
            base_temp = 20 if not self.current_weather else self.current_weather['main']['temp']
            base_humidity = 50 if not self.current_weather else self.current_weather['main']['humidity']
            
            # Simulate fluctuating data
            temp_variation = np.sin(time.time() * 0.1) * 2 + np.random.normal(0, 0.5)
            humidity_variation = np.cos(time.time() * 0.15) * 5 + np.random.normal(0, 1)
            
            new_temp = base_temp + temp_variation
            new_humidity = max(0, min(100, base_humidity + humidity_variation))
            
            self.realtime_data['time'].append(current_time)
            self.realtime_data['temp'].append(new_temp)
            self.realtime_data['humidity'].append(new_humidity)
            
            # Keep only last 50 points
            if len(self.realtime_data['time']) > 50:
                for key in self.realtime_data:
                    self.realtime_data[key] = self.realtime_data[key][-50:]
            
            # Update chart
            self.realtime_ax.clear()
            
            if len(self.realtime_data['time']) > 1:
                # Temperature line
                temp_line = self.realtime_ax.plot(self.realtime_data['time'], self.realtime_data['temp'], 
                                                'r-', linewidth=2, label='Temperature (°C)', alpha=0.8)
                
                # Humidity line (scaled)
                humidity_scaled = [h/5 for h in self.realtime_data['humidity']]  # Scale for better visualization
                humidity_line = self.realtime_ax.plot(self.realtime_data['time'], humidity_scaled, 
                                                    'b-', linewidth=2, label='Humidity (%/5)', alpha=0.8)
                
                self.realtime_ax.set_title('Live Weather Simulation', color='white', fontsize=14, fontweight='bold')
                self.realtime_ax.set_ylabel('Value', color='white')
                self.realtime_ax.tick_params(colors='white')
                self.realtime_ax.grid(True, alpha=0.3, color='white')
                self.realtime_ax.legend()
                
                # Format x-axis
                self.realtime_fig.autofmt_xdate()
            
            self.realtime_canvas.draw()
            
            # Schedule next update
            if self.animation_running:
                self.root.after(1000, update_realtime_data)  # Update every second
        
        update_realtime_data()
    
    def toggle_auto_refresh(self):
        if self.auto_refresh.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        if hasattr(self, 'refresh_job'):
            self.root.after_cancel(self.refresh_job)
        
        def auto_refresh():
            if self.auto_refresh.get() and self.city_entry.get().strip():
                self.get_weather()
            if self.auto_refresh.get():
                self.refresh_job = self.root.after(30000, auto_refresh)  # 30 seconds
        
        self.refresh_job = self.root.after(30000, auto_refresh)
    
    def stop_auto_refresh(self):
        if hasattr(self, 'refresh_job'):
            self.root.after_cancel(self.refresh_job)

def main():
    root = tk.Tk()
    app = AdvancedWeatherApp(root)
    
    # Set window icon and styling
    root.iconname("Weather App")
    
    # Handle window closing
    def on_closing():
        app.animation_running = False
        if hasattr(app, 'refresh_job'):
            root.after_cancel(app.refresh_job)
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start with a sample city
    app.city_entry.insert(0, "London")
    
    root.mainloop()

if __name__ == "__main__":
    main()
