import customtkinter as ctk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import PLOT_BG_COLOR, ORBIT_PATH_COLOR, SATELLITE_COLOR, EARTH_COLOR

class OrbitSimulationFrame(ctk.CTkFrame):
    """
    A high-performance GUI frame for simulating and visualizing a satellite's orbit.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Plot Frame ---
        self.plot_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.plot_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.fig = Figure(figsize=(7, 7), dpi=100, facecolor=PLOT_BG_COLOR)
        self.axes = self.fig.add_subplot(111, projection='3d')
        self.axes.set_facecolor(PLOT_BG_COLOR)
        self.axes.set_title("Orbital Simulation", color='white')
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        self.axes.tick_params(axis='z', colors='white')
        self.axes.set_xlabel("X (km)", color='white')
        self.axes.set_ylabel("Y (km)", color='white')
        self.axes.set_zlabel("Z (km)", color='white')
        self.axes.grid(False)

        # Draw a small Earth sphere at the center
        u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
        x_e = 6371 * np.cos(u) * np.sin(v)
        y_e = 6371 * np.sin(u) * np.sin(v)
        z_e = 6371 * np.cos(v)
        self.axes.plot_surface(x_e, y_e, z_e, color=EARTH_COLOR, alpha=0.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # --- Control Frame ---
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.control_frame.grid_rowconfigure((0, 2, 4), weight=0)
        self.control_frame.grid_rowconfigure((1, 3, 5), weight=1)

        # Sliders for orbital parameters
        self.alt_label = ctk.CTkLabel(self.control_frame, text="Altitude: 7000 km", font=("Roboto", 14))
        self.alt_label.grid(row=0, column=0, pady=(10, 0), sticky="ew")
        self.altitude_slider = ctk.CTkSlider(self.control_frame, from_=500, to=40000, command=lambda val: self.update_plot(val, self.alt_label, "Altitude"))
        self.altitude_slider.set(7000)
        self.altitude_slider.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.inc_label = ctk.CTkLabel(self.control_frame, text="Inclination: 45°", font=("Roboto", 14))
        self.inc_label.grid(row=2, column=0, pady=(10, 0), sticky="ew")
        self.inclination_slider = ctk.CTkSlider(self.control_frame, from_=0, to=90, command=lambda val: self.update_plot(val, self.inc_label, "Inclination"))
        self.inclination_slider.set(45)
        self.inclination_slider.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.ecc_label = ctk.CTkLabel(self.control_frame, text="Eccentricity: 0.2", font=("Roboto", 14))
        self.ecc_label.grid(row=4, column=0, pady=(10, 0), sticky="ew")
        self.ecc_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=lambda val: self.update_plot(val, self.ecc_label, "Eccentricity", 100))
        self.ecc_slider.set(20)
        self.ecc_slider.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        self.path_line, = self.axes.plot([], [], [], color=ORBIT_PATH_COLOR, label='Orbit Path')
        self.satellite_dot, = self.axes.plot([], [], [], 'o', color=SATELLITE_COLOR, markersize=8, label='Satellite')
        
        self._rotation_angle = 0 # New attribute to track rotation
        
        self.compute_orbit(7000, 45, 0.2)
        self.plot_orbit()

    def compute_orbit(self, altitude: float, inclination: float, eccentricity: float) -> None:
        """
        Calculates the 3D coordinates of a simplified elliptical orbit.
        """
        a = 6371 + altitude  # Semi-major axis (assuming circular for now)
        e = eccentricity
        
        # A more realistic orbit calculation is complex. This is a simplified 
        # visualization based on orbital elements for display purposes.
        num_points = 500
        theta = np.linspace(0, 2 * np.pi, num_points)
        r = a * (1 - e**2) / (1 + e * np.cos(theta))

        # Rotate the orbit based on inclination
        inc_rad = np.radians(inclination)
        
        x_prime = r * np.cos(theta)
        y_prime = r * np.sin(theta)
        z_prime = np.zeros(num_points)
        
        self.x = x_prime
        self.y = y_prime * np.cos(inc_rad) - z_prime * np.sin(inc_rad)
        self.z = y_prime * np.sin(inc_rad) + z_prime * np.cos(inc_rad)
    
    def plot_orbit(self) -> None:
        """Updates the plot with the new orbit data and applies rotation."""
        self.path_line.set_data_3d(self.x, self.y, self.z)
        
        # Increment the rotation angle for the satellite dot
        self._rotation_angle = (self._rotation_angle + 1) % len(self.x)

        # Plot the satellite dot at the current rotation position
        self.satellite_dot.set_data_3d([self.x[self._rotation_angle]], [self.y[self._rotation_angle]], [self.z[self._rotation_angle]])

        # Autoscale the plot to fit the new orbit
        max_range = np.max([self.x.max() - self.x.min(), self.y.max() - self.y.min(), self.z.max() - self.z.min()]) / 2.0
        mid_x, mid_y, mid_z = np.mean(self.x), np.mean(self.y), np.mean(self.z)
        self.axes.set_xlim(mid_x - max_range, mid_x + max_range)
        self.axes.set_ylim(mid_y - max_range, mid_y + max_range)
        self.axes.set_zlim(mid_z - max_range, mid_z + max_range)

        # Redraw only the canvas, which is much faster
        self.canvas.draw()
        
    def set_orbital_parameters(self, altitude: float, inclination: float, eccentricity: float) -> None:
        """
        Receives and updates the plot based on new orbital parameters from the main loop.
        """
        # Set slider values and update their labels
        self.altitude_slider.set(altitude)
        self.inc_label.configure(text=f"Altitude: {int(altitude)} km")
        self.inclination_slider.set(inclination)
        self.inc_label.configure(text=f"Inclination: {int(inclination)}°")
        self.ecc_slider.set(eccentricity * 100)
        self.ecc_label.configure(text=f"Eccentricity: {eccentricity:.2f}")

        # Re-compute and re-plot the orbit
        self.compute_orbit(altitude, inclination, eccentricity)
        self.plot_orbit()

    def update_plot(self, val=None, label_widget=None, text_prefix=None, scale=1) -> None:
        """Callback to re-compute and plot the orbit when sliders change."""
        if label_widget and text_prefix:
            if scale == 1:
                label_widget.configure(text=f"{text_prefix}: {int(float(val))}")
            else:
                label_widget.configure(text=f"{text_prefix}: {float(val)/scale:.2f}")

        alt_val = self.altitude_slider.get()
        inc_val = self.inclination_slider.get()
        ecc_val = self.ecc_slider.get() / 100.0

        self.compute_orbit(alt_val, inc_val, ecc_val)
        self.plot_orbit()