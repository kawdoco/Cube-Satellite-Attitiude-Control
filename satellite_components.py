import numpy as np
from typing import List, Tuple
import math

class Satellite:
    """
    Represents an autonomous satellite, now based on orbital parameters.
    """
    def __init__(self, initial_altitude: float, initial_inclination: float, initial_eccentricity: float):
        # We now store orbital parameters directly
        self._altitude = initial_altitude
        self._inclination = initial_inclination
        self._eccentricity = initial_eccentricity

        # This is a mock location for display purposes, as the simulation now
        # operates purely on orbital parameters.
        self._current_location = np.array([0.0, 0.0, 0.0])
        
        # A flag to control the simulation behavior
        self._is_in_orbit_mode = True

    def get_location(self) -> np.ndarray:
        """
        Returns a mock location for display purposes, derived from orbital parameters.
        In a real system, this would be a more complex calculation.
        """
        # A simple, illustrative transformation. Not a true orbital mechanics model.
        r = 6371 + self._altitude
        x = r * math.cos(math.radians(self._inclination))
        y = r * math.sin(math.radians(self._inclination))
        z = r * self._eccentricity * 1000 # Just a simple scaling for visualization
        self._current_location = np.array([x, y, z])
        return self._current_location

    def get_orbital_parameters(self) -> Tuple[float, float, float]:
        """Returns the current altitude, inclination, and eccentricity."""
        return (self._altitude, self._inclination, self._eccentricity)
        
    def get_altitude(self) -> float:
        return self._altitude
        
    def get_inclination(self) -> float:
        return self._inclination
        
    def get_eccentricity(self) -> float:
        return self._eccentricity

    def simulate_orbital_drift(self) -> None:
        """Simulates gradual orbital drift, but only for altitude."""
        # Only altitude drifts due to gravitational pull
        self._altitude -= np.random.uniform(0.01, 0.05)
        # Inclination and eccentricity are stable in this model
        self._inclination = self._inclination
        self._eccentricity = self._eccentricity

    def apply_orbital_correction(self, correction_vector: List[float]) -> None:
        """
        Applies a correction vector, but only to altitude.
        Args:
            correction_vector: The vector from the PID controller.
        """
        self._altitude += correction_vector[0]
        self._inclination = self._inclination
        self._eccentricity = self._eccentricity

class Thruster:
    """The Thruster class is no longer needed in this orbital model as corrections are applied directly."""
    def apply_thrust(self, satellite: Satellite, correction_vector: List[float]) -> np.ndarray:
        """Kept for compatibility, but logic is now handled in the main loop."""
        return satellite.get_location()

class Sensor:
    """
    Simulates a sensor that provides the satellite's current orbital parameters.
    """
    def __init__(self, satellite: Satellite):
        self._satellite = satellite

    def get_current_orbital_parameters(self) -> Tuple[float, float, float]:
        """Returns the satellite's current orbital parameters with simulated noise."""
        true_params = self._satellite.get_orbital_parameters()
        noise = np.random.normal(0, 0.01, 3)  # Add noise to each parameter
        sensed_params = (true_params[0] + noise[0],
                         true_params[1] + noise[1],
                         true_params[2] + noise[2])
        return sensed_params
