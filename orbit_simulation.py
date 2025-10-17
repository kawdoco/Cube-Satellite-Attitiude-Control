import customtkinter as ctk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from config import PLOT_BG_COLOR, ORBIT_PATH_COLOR, SATELLITE_COLOR, EARTH_COLOR, TARGET_ALTITUDE, TARGET_INCLINATION, TARGET_ECCENTRICITY

class OrbitSimulationFrame(ctk.CTkFrame):
    """
    A high-performance GUI frame for simulating and visualizing a satellite's orbit.
    Now includes controls to send new target parameters back to the main application
    and features a smooth, high-framerate animation for the satellite cube.
    """
    def __init__(self, master, on_update_target: callable = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_update_target = on_update_target

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Plot Frame ---
        self.plot_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.plot_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.fig = Figure(figsize=(7, 7), dpi=100, facecolor=PLOT_BG_COLOR)
        self.axes = self.fig.add_subplot(111, projection='3d')
        self._setup_plot_aesthetics()

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
        self._setup_controls()

        self.path_line, = self.axes.plot([], [], [], color=ORBIT_PATH_COLOR, label='Orbit Path')
        
        # --- Satellite Cube Definition ---
        cube_size = 1200  # Size of the cube in km to be visible
        r = [-cube_size / 2, cube_size / 2]
        self.cube_vertices = np.array(list(np.broadcast(*np.ix_(r, r, r))))
        self.cube_faces = [
            [self.cube_vertices[0], self.cube_vertices[1], self.cube_vertices[3], self.cube_vertices[2]],
            [self.cube_vertices[4], self.cube_vertices[5], self.cube_vertices[7], self.cube_vertices[6]],
            [self.cube_vertices[0], self.cube_vertices[1], self.cube_vertices[5], self.cube_vertices[4]],
            [self.cube_vertices[2], self.cube_vertices[3], self.cube_vertices[7], self.cube_vertices[6]],
            [self.cube_vertices[0], self.cube_vertices[2], self.cube_vertices[6], self.cube_vertices[4]],
            [self.cube_vertices[1], self.cube_vertices[3], self.cube_vertices[7], self.cube_vertices[5]],
        ]
        self.satellite_cube = Poly3DCollection(self.cube_faces, facecolors=SATELLITE_COLOR, linewidths=1, edgecolors='darkred')
        self.axes.add_collection3d(self.satellite_cube)
        
        self.axes.plot([],[],[], color=SATELLITE_COLOR, marker='s', markersize=5, linestyle='None', label='Satellite')
        self.axes.legend()

        # --- Animation & State Variables ---
        self._rotation_angle = 0  # Index for position on the orbit path
        self._cube_rotation_angle_y = 0
        self._cube_rotation_angle_z = 0
        self._speed = 1
        self.satellite_pos = np.array([0.0, 0.0, 0.0]) # Current satellite coordinates
        self.x, self.y, self.z = [], [], [] # Stores orbit path coordinates
        
        # Initialize with default orbit. This updates self.x, self.y, self.z and self.satellite_pos
        self.set_orbital_parameters(TARGET_ALTITUDE, TARGET_INCLINATION, TARGET_ECCENTRICITY, initial_setup=True)
        
        # Start the high-frequency animation loop
        self._animate()

    def _setup_plot_aesthetics(self):
        """Configures the visual style of the 3D plot."""
        self.axes.set_facecolor(PLOT_BG_COLOR)
        self.axes.set_title("Orbital Simulation", color='white')
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        self.axes.tick_params(axis='z', colors='white')
        self.axes.set_xlabel("X (km)", color='white')
        self.axes.set_ylabel("Y (km)", color='white')
        self.axes.set_zlabel("Z (km)", color='white')
        self.axes.grid(False)

    def _setup_controls(self):
        """Creates the sliders and buttons for controlling the simulation view and targets."""
        self.control_frame.grid_rowconfigure((0, 2, 4, 6, 7, 9), weight=0)
        self.control_frame.grid_rowconfigure((1, 3, 5, 8, 10), weight=1)

        self.alt_label = ctk.CTkLabel(self.control_frame, text=f"Altitude: {int(TARGET_ALTITUDE)} km", font=("Roboto", 14))
        self.alt_label.grid(row=0, column=0, pady=(10, 0), sticky="ew")
        self.altitude_slider = ctk.CTkSlider(self.control_frame, from_=500, to=40000, command=lambda v: self._update_label_text(self.alt_label, "Altitude", f"{int(float(v))} km"))
        self.altitude_slider.set(TARGET_ALTITUDE)
        self.altitude_slider.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.inc_label = ctk.CTkLabel(self.control_frame, text=f"Inclination: {int(TARGET_INCLINATION)}°", font=("Roboto", 14))
        self.inc_label.grid(row=2, column=0, pady=(10, 0), sticky="ew")
        self.inclination_slider = ctk.CTkSlider(self.control_frame, from_=0, to=90, command=lambda v: self._update_label_text(self.inc_label, "Inclination", f"{int(float(v))}°"))
        self.inclination_slider.set(TARGET_INCLINATION)
        self.inclination_slider.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.ecc_label = ctk.CTkLabel(self.control_frame, text=f"Eccentricity: {TARGET_ECCENTRICITY:.2f}", font=("Roboto", 14))
        self.ecc_label.grid(row=4, column=0, pady=(10, 0), sticky="ew")
        self.ecc_slider = ctk.CTkSlider(self.control_frame, from_=0, to=99, command=lambda v: self._update_label_text(self.ecc_label, "Eccentricity", f"{float(v)/100.0:.2f}"))
        self.ecc_slider.set(TARGET_ECCENTRICITY * 100)
        self.ecc_slider.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        # Button to send the new target parameters to the main simulation
        self.set_target_button = ctk.CTkButton(self.control_frame, text="Set New Target Orbit", command=self.send_new_target_parameters)
        self.set_target_button.grid(row=6, column=0, padx=10, pady=15, sticky="ew")
        
        # Button to correct the orbit to its default state
        self.correct_orbit_button = ctk.CTkButton(self.control_frame, text="Correct the Orbit", command=self.correct_orbit)
        self.correct_orbit_button.grid(row=7, column=0, padx=10, pady=5, sticky="ew")

        self.speed_label = ctk.CTkLabel(self.control_frame, text="Animation Speed: 1x", font=("Roboto", 14))
        self.speed_label.grid(row=8, column=0, pady=(10, 0), sticky="ew")
        self.speed_slider = ctk.CTkSlider(self.control_frame, from_=1, to=10, number_of_steps=9, command=self.update_speed)
        self.speed_slider.set(1)
        self.speed_slider.grid(row=9, column=0, padx=10, pady=5, sticky="ew")

    def _update_label_text(self, label_widget, prefix, value_str):
        """Updates the text of a label widget."""
        label_widget.configure(text=f"{prefix}: {value_str}")

    def send_new_target_parameters(self):
        """Gets values from sliders and sends them to the main app via callback."""
        if self.on_update_target:
            alt = self.altitude_slider.get()
            inc = self.inclination_slider.get()
            ecc = self.ecc_slider.get() / 100.0
            self.on_update_target(alt, inc, ecc)

    def correct_orbit(self):
        """Resets the orbit controls to default values and sets them as the new target."""
        # Set slider values
        self.altitude_slider.set(TARGET_ALTITUDE)
        self.inclination_slider.set(TARGET_INCLINATION)
        self.ecc_slider.set(TARGET_ECCENTRICITY * 100)

        # Update label texts to match the new slider values
        self._update_label_text(self.alt_label, "Altitude", f"{int(TARGET_ALTITUDE)} km")
        self._update_label_text(self.inc_label, "Inclination", f"{int(TARGET_INCLINATION)}°")
        self._update_label_text(self.ecc_label, "Eccentricity", f"{TARGET_ECCENTRICITY:.2f}")
        
        # Send these default parameters as the new target for the simulation
        self.send_new_target_parameters()

    def update_speed(self, val: float) -> None:
        """Updates the satellite's animation speed."""
        self._speed = int(val)
        self.speed_label.configure(text=f"Animation Speed: {self._speed}x")

    def compute_orbit(self, altitude: float, inclination: float, eccentricity: float) -> None:
        """Calculates the 3D coordinates of a simplified elliptical orbit for visualization."""
        a = 6371 + altitude
        e = eccentricity
        num_points = 500
        theta = np.linspace(0, 2 * np.pi, num_points)
        r = a * (1 - e**2) / (1 + e * np.cos(theta))
        inc_rad = np.radians(inclination)
        
        x_prime = r * np.cos(theta)
        y_prime = r * np.sin(theta)
        z_prime = np.zeros(num_points)
        
        self.x = x_prime
        self.y = y_prime * np.cos(inc_rad) - z_prime * np.sin(inc_rad)
        self.z = y_prime * np.sin(inc_rad) + z_prime * np.cos(inc_rad)

    def _animate(self) -> None:
        """High-frequency animation loop for smooth cube rotation and redrawing."""
        # Update the cube's independent rotation angles with small increments for smoothness
        self._cube_rotation_angle_y = (self._cube_rotation_angle_y + 1.5) % 360
        self._cube_rotation_angle_z = (self._cube_rotation_angle_z + 0.75) % 360

        # Create rotation matrices
        angle_y = np.radians(self._cube_rotation_angle_y)
        cy, sy = np.cos(angle_y), np.sin(angle_y)
        R_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])

        angle_z = np.radians(self._cube_rotation_angle_z)
        cz, sz = np.cos(angle_z), np.sin(angle_z)
        R_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])

        # Rotate the base vertices and then translate to the current satellite position
        rotated_vertices = self.cube_vertices @ R_y @ R_z
        translated_vertices = rotated_vertices + self.satellite_pos

        # Rebuild the list of face vertices for the collection
        new_faces = [
            [translated_vertices[0], translated_vertices[1], translated_vertices[3], translated_vertices[2]],
            [translated_vertices[4], translated_vertices[5], translated_vertices[7], translated_vertices[6]],
            [translated_vertices[0], translated_vertices[1], translated_vertices[5], translated_vertices[4]],
            [translated_vertices[2], translated_vertices[3], translated_vertices[7], translated_vertices[6]],
            [translated_vertices[0], translated_vertices[2], translated_vertices[6], translated_vertices[4]],
            [translated_vertices[1], translated_vertices[3], translated_vertices[7], translated_vertices[5]],
        ]

        # Update the cube's vertex data and redraw the canvas
        self.satellite_cube.set_verts(new_faces)
        self.canvas.draw()
        
        # Schedule the next animation frame for a target of ~60 FPS
        self.after(16, self._animate)

    def get_current_position(self) -> np.ndarray:
        """Returns the current animated position of the satellite."""
        return self.satellite_pos

    def set_orbital_parameters(self, altitude: float, inclination: float, eccentricity: float, initial_setup: bool = False) -> None:
        """
        Receives and updates the orbit based on new orbital parameters from the main loop.
        This function runs at the simulation tick rate and only updates data, not the view.
        """
        self.compute_orbit(altitude, inclination, eccentricity)
        self.path_line.set_data_3d(self.x, self.y, self.z)

        # Only advance the satellite's position along the orbit if it's not the initial setup call.
        if not initial_setup and len(self.x) > 0:
            self._rotation_angle = (self._rotation_angle + self._speed) % len(self.x)
        
        # Update the satellite's target position for the animation loop to use
        if len(self.x) > 0:
            self.satellite_pos = np.array([self.x[self._rotation_angle], self.y[self._rotation_angle], self.z[self._rotation_angle]])

        # Auto-adjust plot limits when the orbit changes
        if len(self.x) > 0:
            max_range = np.max([self.x.max() - self.x.min(), self.y.max() - self.y.min(), self.z.max() - self.z.min()]) / 2.0
            mid_x, mid_y, mid_z = np.mean(self.x), np.mean(self.y), np.mean(self.z)
            self.axes.set_xlim(mid_x - max_range, mid_x + max_range)
            self.axes.set_ylim(mid_y - max_range, mid_y + max_range)
            self.axes.set_zlim(mid_z - max_range, mid_z + max_range)

