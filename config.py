"""
config.py

Centralized configuration file for the CubeSat Mission Control application.
Stores constants and settings to make the application easier to manage and tune.
"""
from pathlib import Path

# --- DIRECTORY PATHS ---
# Defines a base path to the 'assets' directory relative to the login script.
# This makes the application portable and prevents path errors on different computers.
ASSETS_PATH = Path(__file__).parent / "assets"
# Path to the application icon.
APP_ICON_FILENAME = "satellite_icon.ico"
ICON_PATH = ASSETS_PATH / APP_ICON_FILENAME

# --- SIMULATION PARAMETERS ---
SIMULATION_TICK_RATE_HZ = 1  # How many times the main loop runs per second
ON_COURSE_THRESHOLD = 0.1  # Distance from target to be considered "On Course"

# Target Orbital Parameters
TARGET_ALTITUDE = 8000.0  # Target altitude in kilometers
TARGET_INCLINATION = 45.0 # Target inclination in degrees
TARGET_ECCENTRICITY = 0.2 # Target orbital eccentricity

# --- PID CONTROLLER GAINS ---
# These values determine how the satellite corrects its course.
# Kp: Proportional gain (reacts to current error)
# Ki: Integral gain (corrects long-term error)
# Kd: Derivative gain (dampens oscillations)
PID_GAINS = {'Kp': 0.5, 'Ki': 0.01, 'Kd': 0.1}

# --- DATA & LOGGING LIMITS ---
# Using a fixed size prevents memory usage from growing infinitely.
TELEMETRY_LOG_MAX_SIZE = 1000
HISTORY_LOG_MAX_SIZE = 500
PLOT_DATA_MAX_POINTS = 100  # Max points to show on live graphs

# --- GUI APPEARANCE & THEME ---
# Colors are centralized here for easy theme changes.
APP_THEME_MODE = "dark"  # "dark" or "light"
APP_COLOR_THEME = "blue"  # Custom color theme

# Specific colors for GUI elements
DANGER_COLOR = "#b30000"
DANGER_HOVER_COLOR = "#e60000"

# Plotting colors
PLOT_BG_COLOR = "#2b2b2b"
CORRECTION_PLOT_COLOR = "#3366cc"
DRIFT_PLOT_COLOR = "#cc3333"

# Orbit simulation colors
ORBIT_PATH_COLOR = "#0D9F00"
SATELLITE_COLOR = "#ff7700"  # Changed from yellow to red for the cube
EARTH_COLOR = "#0052cc"

# Login Page Background Image
LOGIN_BG_IMAGE_FILENAME = "login.png"
