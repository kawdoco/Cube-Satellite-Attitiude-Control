"""
orbit_simulation.py

A GUI frame for visualizing a satellite's orbit in 3D.
Optimized to animate plots efficiently by updating data instead of redrawing.
"""
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
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

        # --- Control Frame ---
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self._setup_controls()

        # --- Orbit Parameters ---
        self.R_earth = 6371  # Radius of Earth in km
        self.theta_index = 0
        self.num_points = 360

        # --- OPTIMIZATION: Create plot elements once ---
        self._setup_plot_elements()

        # Initial plot generation
        self.update_plot()
        self.animate_satellite()

    def _setup_controls(self) -> None:
        """Initializes all the control sliders and labels."""
        ctk.CTkLabel(self.controls_frame, text="Orbit Parameters", font=("Roboto", 16, "bold")).pack(pady=10)

        self.altitude_slider = self._create_slider("Altitude (km)", 300, 40000, 7000)
        self.inclination_slider = self._create_slider("Inclination (°)", 0, 90, 45)
        self.ecc_slider = self._create_slider("Eccentricity (x100)", 0, 90, 20)

    def _create_slider(self, text: str, from_: int, to: int, initial_val: int) -> ctk.CTkSlider:
        """Helper to create a labeled slider."""
        frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        label = ctk.CTkLabel(frame, text=f"{text}: {initial_val}")
        label.pack(fill='x', padx=5)
        slider = ctk.CTkSlider(frame, from_=from_, to=to, command=lambda val, l=label, t=text: self.update_plot(val, l, t))
        slider.set(initial_val)
        slider.pack(fill='x', expand=True, padx=5, pady=(0, 10))
        frame.pack(fill='x', pady=5)
        return slider

    def _setup_plot_elements(self) -> None:
        """Initializes static and dynamic plot elements for efficient animation."""
        # --- Static Earth Sphere ---
        u, v = np.mgrid[0:2*np.pi:40j, 0:np.pi:20j]
        xe = self.R_earth * np.cos(u) * np.sin(v)
        ye = self.R_earth * np.sin(u) * np.sin(v)
        ze = self.R_earth * np.cos(v)
        self.axes.plot_surface(xe, ye, ze, color=EARTH_COLOR, alpha=0.6, rstride=2, cstride=2)

        # --- Dynamic Elements (placeholders) ---
        self.orbit_line, = self.axes.plot([], [], [], ORBIT_PATH_COLOR, label="Orbit Path", linewidth=2)
        self.satellite_scatter = self.axes.scatter([], [], [], color=SATELLITE_COLOR, s=80, depthshade=True, label="Satellite")

        # --- Static Axis Setup ---
        self.axes.set_xlabel("X (km)", color='white', fontsize=10)
        self.axes.set_ylabel("Y (km)", color='white', fontsize=10)
        self.axes.set_zlabel("Z (km)", color='white', fontsize=10)
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        self.axes.tick_params(axis='z', colors='white')
        self.fig.tight_layout()

    def compute_orbit(self, altitude: float, inclination: float, eccentricity: float) -> None:
        """Computes the 3D coordinates of the orbit."""
        a = self.R_earth + altitude
        theta = np.linspace(0, 2 * np.pi, self.num_points)
        r = a * (1 - eccentricity**2) / (1 + eccentricity * np.cos(theta))
        self.x = r * np.cos(theta)
        self.y = r * np.sin(theta)
        self.z = np.zeros_like(self.x)

        inc_rad = np.deg2rad(inclination)
        self.y = self.y * np.cos(inc_rad)
        self.z = r * np.sin(theta) * np.sin(inc_rad)

    def plot_orbit(self) -> None:
        """
        OPTIMIZED: Updates the data of existing plot elements instead of redrawing.
        """
        # Update orbit path data
        self.orbit_line.set_data(self.x, self.y)
        self.orbit_line.set_3d_properties(self.z)

        # Update satellite position data
        idx = self.theta_index % self.num_points
        self.satellite_scatter._offsets3d = ([self.x[idx]], [self.y[idx]], [self.z[idx]])

        # Rescale axes to fit the new orbit
        max_range = np.max([self.x.max() - self.x.min(), self.y.max() - self.y.min(), self.z.max() - self.z.min()]) / 2.0
        mid_x, mid_y, mid_z = np.mean(self.x), np.mean(self.y), np.mean(self.z)
        self.axes.set_xlim(mid_x - max_range, mid_x + max_range)
        self.axes.set_ylim(mid_y - max_range, mid_y + max_range)
        self.axes.set_zlim(mid_z - max_range, mid_z + max_range)

        # Redraw only the canvas, which is much faster
        self.canvas.draw()

    def update_plot(self, val=None, label_widget=None, text_prefix=None) -> None:
        """Callback to re-compute and plot the orbit when sliders change."""
        if label_widget and text_prefix:
            label_widget.configure(text=f"{text_prefix}: {int(float(val))}")

        alt_val = self.altitude_slider.get()
        inc_val = self.inclination_slider.get()
        ecc_val = self.ecc_slider.get() / 100.0

        self.compute_orbit(alt_val, inc_val, ecc_val)
        self.plot_orbit()

    def animate_satellite(self) -> None:
        """Animates the satellite's movement along the pre-computed orbit."""
        self.theta_index += 1
        idx = self.theta_index % self.num_points

        # OPTIMIZED: Only update the satellite's 3D position
        self.satellite_scatter._offsets3d = ([self.x[idx]], [self.y[idx]], [self.z[idx]])
        self.canvas.draw_idle()  # Use draw_idle for smoother animation

        self.after(50, self.animate_satellite)
