import customtkinter as ctk
import numpy as np
from config import (
    ORBIT_PATH_COLOR, 
    # EARTH_COLOR, # No longer used
    PLANET_DATA, # Import new planet data
    TARGET_ALTITUDE, 
    TARGET_INCLINATION, 
    TARGET_ECCENTRICITY,
    SATELLITE_COLOR,
    SATELLITE_OUTLINE_COLOR
)

class OrbitSimulationFrame(ctk.CTkFrame):
    """
    A high-performance GUI frame for visualizing a satellite's orbit
    using a 2D Tkinter Canvas for a top-down view. 
    Now features animated backgrounds.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Background and Star Colors ---
        self.bg_color = "black"
        self.dark_bg_star_colors = ["#FFFFFF", "#AAAAAA", "#CCCCCC", "#999999"]
        self.current_star_colors = self.dark_bg_star_colors
        
        # --- NEW: Animation State ---
        self.current_bg_animation = "static" # "static", "twinkle", "streak"
        self.stars = [] # List of star data dicts
        self.star_canvas_items = [] # List of canvas item IDs
        self.num_stars = 300

        # --- 2D Simulation Canvas ---
        self.canvas = ctk.CTkCanvas(self, bg=self.bg_color, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # --- Canvas Size & Elements ---
        self.width, self.height = 700, 700
        self.center_x, self.center_y = 350, 350
        
        # --- Planet Data ---
        self.current_planet_data = None
        
        # This call will load "Earth" data and colors
        self.set_planet("Earth", initial_setup=True) 

        self.earth_ocean_item = self.canvas.create_oval(0, 0, 0, 0, fill=self.current_planet_data["color"], outline="")
        
        # --- Earth Rotation Elements ("Dual Rotation" Part 1) ---
        self.continent_items = []
        # Base continent shapes are now loaded from self.current_planet_data in _on_canvas_resize
        self.base_continent_shapes_scaled = [] # To store scaled (but not centered) shapes
        self._earth_rotation_angle = 0.0

        # --- Satellite & Orbit Path ---
        self.orbit_path_item = self.canvas.create_polygon([0, 0], fill="", outline=ORBIT_PATH_COLOR, width=2, tag="orbit_path")
        
        # --- Satellite Spin Elements ("Dual Rotation" Part 2) ---
        # This shape defines a "real" CubeSat: a central body with two solar panels.
        self.satellite_base_shape = np.array([
            [-4, -2], [4, -2], [4, 2], [-4, 2], # Body
            [4, -1], [8, -3], [8, 3], [4, 1], # Panel 1
            [-4, -1], [-8, -3], [-8, 3], [-4, 1]  # Panel 2
        ]) * 2.0 # <-- FIX 1: Increased satellite size (from 1.2 to 2.0)
        
        self._satellite_spin_angle = 0.0
        # Create as a polygon instead of a rectangle
        self.satellite_item = self.canvas.create_polygon([0,0], fill=SATELLITE_COLOR, outline=SATELLITE_OUTLINE_COLOR, tag="satellite")

        # Bind resize event
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # --- Zoom Controls ---
        self.zoom_level = 1.0
        self.canvas.bind("<MouseWheel>", self._on_zoom)  # Windows/macOS
        self.canvas.bind("<Button-4>", self._on_zoom)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_zoom)  # Linux scroll down

        # --- Animation & State Variables ---
        self._rotation_angle = 0.0 # Use float for smoother speed changes
        self._speed = 1.0
        self.satellite_pos_3d = np.array([0.0, 0.0, 0.0])
        self.x, self.y, self.z = [], [], []
        
        # --- FIX 2: Add animation state variable ---
        self.is_animating = False # Start in a paused state

        self.set_orbital_parameters(TARGET_ALTITUDE, TARGET_INCLINATION, TARGET_ECCENTRICITY, initial_setup=True)
        
        # --- FIX 2: Start the _animate loop, but it will be idle ---
        self._animate() 

    # --- NEW: Star Creation Method ---
    def _create_stars(self):
        """Clears and redraws the starfield based on current settings."""
        # Clear existing stars
        for item_id in self.star_canvas_items:
            self.canvas.delete(item_id)
        self.stars.clear()
        self.star_canvas_items.clear()
        
        if self.width <= 1 or self.height <= 1: return # Avoid error on minimize
        
        for _ in range(self.num_stars):
            # Use uniform distribution for more natural star placement
            x = np.random.uniform(0, self.width)
            y = np.random.uniform(0, self.height)
            z = np.random.uniform(0.1, 1.0) # z-depth for parallax
            
            # Closer stars (lower z) are slightly bigger
            size = (1.1 - z) * 2.5 
            color = np.random.choice(self.current_star_colors)
            
            item_id = self.canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")
            
            # Store star data for animation
            self.stars.append({
                "id": item_id, 
                "x": x, "y": y, "z": z, 
                "size": size, 
                "base_color": color
            })
            self.star_canvas_items.append(item_id)

    def _on_canvas_resize(self, event):
        """Redraws static elements (stars, Earth) when the canvas size changes."""
        
        # If event is None (from a fake call), use existing width/height
        if event:
            self.width = event.width
            self.height = event.height
        
        self.center_x, self.center_y = self.width / 2, self.height / 2
        
        # --- MODIFIED: Re-create starfield ---
        self._create_stars()
            
        # --- (THE FIX) ---
        # Calculate the scale factor based on the *current* orbit
        scale_factor = self._get_scale_factor()
        
        # Earth's REAL radius is read from planet data
        earth_radius_km = self.current_planet_data["radius_km"]
        earth_radius = earth_radius_km * scale_factor
        
        # Clip the radius so it doesn't get too small or big
        earth_radius = np.clip(earth_radius, 5.0, min(self.width, self.height) * 0.45)
            
        # --- Redraw Earth Ocean ---
        self.canvas.coords(self.earth_ocean_item, self.center_x - earth_radius, self.center_y - earth_radius, self.center_x + earth_radius, self.center_y + earth_radius)
        
        # --- Redraw Earth Continents ---
        land_radius = earth_radius * 0.9 # This now scales relatively
        
        # Delete old continent items
        for item in self.continent_items: self.canvas.delete(item)
        self.continent_items.clear()
        self.base_continent_shapes_scaled.clear()

        # Re-create continents based on new size from planet data
        for shape_norm in self.current_planet_data["continents"]:
            shape_scaled = shape_norm * land_radius
            self.base_continent_shapes_scaled.append(shape_scaled)
            shape_centered = shape_scaled + np.array([self.center_x, self.center_y])
            item = self.canvas.create_polygon(shape_centered.flatten().tolist(), fill=self.current_planet_data["land_color"], outline="")
            self.continent_items.append(item)
        
        # Force redraw of continents at current rotation
        self._update_earth_rotation(force_redraw=True) 
        
        # Redraw the orbit path to fit the new canvas size
        self._update_orbit_path_on_canvas()

    def _update_earth_rotation(self, force_redraw=False):
        """Rotates the continent polygons."""
        if not hasattr(self, 'base_continent_shapes_scaled') or not self.continent_items:
            return

        # Increment angle (slowly)
        if not force_redraw:
            self._earth_rotation_angle += 0.003 # Radians per frame
        
        angle_rad = self._earth_rotation_angle
        c, s = np.cos(angle_rad), np.sin(angle_rad)
        cx, cy = self.center_x, self.center_y
        
        # Apply rotation to each continent
        for base_shape, item in zip(self.base_continent_shapes_scaled, self.continent_items):
            rotated_coords = []
            for x, y in base_shape:
                x_rot = x * c - y * s
                y_rot = x * s + y * c
                rotated_coords.extend([x_rot + cx, y_rot + cy])
            
            self.canvas.coords(item, *rotated_coords)
            self.canvas.tag_lower(item, self.orbit_path_item) # Keep continents under orbit path

    def _on_zoom(self, event):
        """Handles mouse wheel scrolling to zoom in and out."""
        if event.delta > 0 or event.num == 4:
            self.zoom_level *= 1.1  # Zoom in
        elif event.delta < 0 or event.num == 5:
            self.zoom_level /= 1.1  # Zoom out
        self.zoom_level = np.clip(self.zoom_level, 0.1, 20.0) # Clamp zoom
        
        # Force a redraw of static elements with new zoom
        # We pass None so _on_canvas_resize uses the existing canvas width/height
        self._on_canvas_resize(event=None)

    # --- MODIFIED: Set Background Method ---
    def set_background(self, bg_name: str):
        """Updates the canvas background color and star colors."""
        if bg_name == "Black":
            self.bg_color = "black"
            self.current_star_colors = self.dark_bg_star_colors
            self.current_bg_animation = "static"
        elif bg_name == "Dark Blue":
            self.bg_color = "#000020" # A very dark navy blue
            self.current_star_colors = self.dark_bg_star_colors
            self.current_bg_animation = "twinkle"
        elif bg_name == "Starfield":
            self.bg_color = "#100010" # A dark purple/black
            self.current_star_colors = self.dark_bg_star_colors
            self.current_bg_animation = "streak"
        else:
            return # Unknown name

        # Apply the new background color to the canvas
        self.canvas.configure(bg=self.bg_color)
        
        # Force a redraw of the canvas to update the stars
        self._on_canvas_resize(event=None)
    # --- END MODIFIED ---

    def set_planet(self, planet_name: str, initial_setup: bool = False):
        """Loads data for a new planet and redraws it."""
        if planet_name not in PLANET_DATA:
            print(f"Error: Planet '{planet_name}' not found in config.")
            return
        
        self.current_planet_data = PLANET_DATA[planet_name]
        
        # Update ocean color
        if hasattr(self, 'earth_ocean_item'):
             self.canvas.itemconfig(self.earth_ocean_item, fill=self.current_planet_data["color"])
        
        # We must force a resize/redraw to rebuild continents and rescale
        if not initial_setup and hasattr(self, 'width'):
            self._on_canvas_resize(event=None)

    def update_speed(self, val: float) -> None:
        """Updates the satellite's animation speed. Called from main.py."""
        self._speed = val

    def compute_orbit(self, altitude: float, inclination: float, eccentricity: float) -> None:
        """Calculates the 3D coordinates of the orbit path."""
        
        # Use the radius of the *current* planet
        planet_radius_km = self.current_planet_data["radius_km"]
        a = planet_radius_km + altitude
        
        e = eccentricity
        num_points = 500
        theta = np.linspace(0, 2 * np.pi, num_points)
        r = a * (1 - e**2) / (1 + e * np.cos(theta))
        inc_rad = np.radians(inclination)
        
        x_prime, y_prime = r * np.cos(theta), r * np.sin(theta)
        
        # Store as lists (as they were in the original)
        self.x = x_prime.tolist()
        self.y = (y_prime * np.cos(inc_rad)).tolist()
        self.z = (y_prime * np.sin(inc_rad)).tolist()

    def _get_scale_factor(self) -> float:
        """Calculates the scaling factor (pixels per km) to fit the orbit to the canvas."""
        if not hasattr(self, 'x') or len(self.x) == 0: 
            # Fallback if orbit isn't computed yet, use default target
            max_orbit_range = self.current_planet_data["radius_km"] + TARGET_ALTITUDE
        else:
            max_orbit_range = max(max(abs(v) for v in self.x), max(abs(v) for v in self.y))
        
        if max_orbit_range == 0: 
            max_orbit_range = 40000 # Failsafe
        
        # Calculate scale: (canvas_size * padding) / (real_size_in_km)
        base_scale = (min(self.width, self.height) * 0.48) / max_orbit_range
        return base_scale * self.zoom_level # Apply zoom
    
    def _scale_point_to_canvas(self, x_3d, y_3d) -> tuple[float, float]:
        """Scales a 3D orbit coordinate to a 2D canvas coordinate."""
        if not hasattr(self, 'x') or len(self.x) == 0 or self.width == 0: 
            return self.center_x, self.center_y
        
        scale_factor = self._get_scale_factor()
        
        return self.center_x + (x_3d * scale_factor), self.center_y - (y_3d * scale_factor)
        
    def _update_orbit_path_on_canvas(self):
        """Redraws the green orbit path line on the canvas."""
        if not hasattr(self, 'x') or len(self.x) == 0 or self.width == 0: 
            return
            
        canvas_points = [coord for x, y in zip(self.x, self.y) for coord in self._scale_point_to_canvas(x, y)]
        self.canvas.coords(self.orbit_path_item, *canvas_points)

    # --- NEW: Background Animation Method ---
    def _animate_background(self):
        """Runs the animation for the currently selected background."""
        
        if self.current_bg_animation == "twinkle":
            # Randomly change the color of 10 stars per frame
            for _ in range(10):
                if not self.stars: return
                star = self.stars[np.random.randint(0, len(self.stars))]
                new_color = np.random.choice(self.dark_bg_star_colors)
                self.canvas.itemconfig(star["id"], fill=new_color)
        
        elif self.current_bg_animation == "streak":
            # Move stars from right to left, wrapping around
            # Scale the speed with the orbit speed slider
            streak_speed = 3.0 * self._speed
            
            for star in self.stars:
                # Move star based on its z-depth (parallax)
                star["x"] -= (streak_speed * star["z"])
                
                # If star goes off-screen left, wrap it to the right
                if star["x"] < -star["size"]:
                    star["x"] = self.width
                    star["y"] = np.random.uniform(0, self.height)
                
                # Update canvas coordinates
                self.canvas.coords(star["id"], star["x"], star["y"], 
                                   star["x"] + star["size"], star["y"] + star["size"])

        elif self.current_bg_animation == "static":
            # Do nothing, stars are static
            pass

    def _animate(self) -> None:
        """High-frequency animation loop for moving the satellite and rotating Earth."""
        
        # --- FIX 2: Only run animation logic if not paused ---
        if self.is_animating:
            
            # --- NEW: Animate Background ---
            self._animate_background()
            
            # --- DUAL ROTATION 1: Rotate Earth ---
            self._update_earth_rotation()
            
            # --- Move Satellite ---
            if hasattr(self, 'x') and len(self.x) > 0:
                self._rotation_angle = (self._rotation_angle + self._speed) % len(self.x)
                angle_int = int(self._rotation_angle)
                
                x_pos_3d, y_pos_3d, z_pos_3d = self.x[angle_int], self.y[angle_int], self.z[angle_int]
                self.satellite_pos_3d = np.array([x_pos_3d, y_pos_3d, z_pos_3d])
                
                canvas_x, canvas_y = self._scale_point_to_canvas(x_pos_3d, y_pos_3d)
                
                # --- DUAL ROTATION 2: Satellite Spin ---
                self._satellite_spin_angle += 0.05 # Radians per frame (spin speed)
                spin_rad = self._satellite_spin_angle
                s, c = np.sin(spin_rad), np.cos(spin_rad)
                
                rot_matrix = np.array([[c, -s], [s, c]])
                rotated_shape = self.satellite_base_shape.dot(rot_matrix)
                final_shape = rotated_shape + np.array([canvas_x, canvas_y])
                
                self.canvas.coords(self.satellite_item, *final_shape.flatten())
                
                # --- (THE FIX) ---
                # self.canvas.tag_raise(self.earth_ocean_item) # <-- REMOVED: This was covering the continents
                # --- (END THE FIX) ---
                
                # Continents are lowered below orbit path in _update_earth_rotation
                
                self.canvas.tag_raise(self.orbit_path_item)
                self.canvas.tag_raise(self.satellite_item)

        # Always schedule the next frame to keep the loop alive
        self.after(16, self._animate) # Target ~60 FPS

    def get_current_position(self) -> np.ndarray:
        """Returns the current 3D position of the satellite for the main plot."""
        return self.satellite_pos_3d

    def set_orbital_parameters(self, altitude: float, inclination: float, eccentricity: float, initial_setup: bool = False) -> None:
        """Updates the orbit path based on new parameters from the main loop."""
        self.compute_orbit(altitude, inclination, eccentricity)
        
        # --- (USER REQUEST FIX) ---
        # Force a full redraw of the canvas, which resizes the planet
        # and then redraws the orbit path.
        # This is called with event=None to use the existing canvas size.
        
        # --- (THE FIX) ---
        self._on_canvas_resize(event=None) # <-- Was 'self_on_canvas_resize'
        # --- (END THE FIX) ---
        
        # self._update_orbit_path_on_canvas() # <-- No longer needed, _on_canvas_resize does this.

        if hasattr(self, 'x') and len(self.x) > 0:
            self._rotation_angle = self._rotation_angle % len(self.x)
        else:
            self._rotation_angle = 0.0

    # --- FIX 2: Add public method to control animation state ---
    def set_animation_state(self, is_running: bool):
        """Public method to start or pause the visual animation."""
        self.is_animating = is_running