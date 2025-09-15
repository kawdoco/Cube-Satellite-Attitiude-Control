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

# --- SIMULATION PARAMETERS ---
INITIAL_TARGET_LOCATION = (100.0, 200.0, 300.0)
SIMULATION_TICK_RATE_HZ = 1  # How many times the main loop runs per second
ON_COURSE_THRESHOLD = 0.1  # Distance from target to be considered "On Course"

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
APP_THEME_MODE = "Dark"
APP_COLOR_THEME = "blue"

# Button Colors
DANGER_COLOR = "#E74C3C"
DANGER_HOVER_COLOR = "#C0392B"

# Plot Colors (Facecolor and Line Colors)
PLOT_BG_COLOR = "#2b2b2b"
CORRECTION_PLOT_COLOR = "cyan"
DRIFT_PLOT_COLOR = "yellow"
ORBIT_PATH_COLOR = "red"
SATELLITE_COLOR = "white"
EARTH_COLOR = "#3b82f6"
