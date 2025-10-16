import numpy as np
from typing import List, Tuple
import math

class Satellite:
    """
    Represents an autonomous satellite, now based on orbital parameters.
    Simulates drift and corrections for altitude, inclination, and eccentricity.
    """
    def __init__(self, initial_altitude: float, initial_inclination: float, initial_eccentricity: float):
        self._altitude = initial_altitude
        self._inclination = initial_inclination
        self._eccentricity = initial_eccentricity
        self._current_location = np.array([0.0, 0.0, 0.0])
        self._is_in_orbit_mode = True

    def get_location(self) -> np.ndarray:
        """
        Returns a mock location for display purposes, derived from orbital parameters.
        In a real system, this would be a more complex calculation.
        """
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
        """
        Simulates gradual, random orbital drift for all key parameters.
        """
        # Altitude drifts due to atmospheric drag and gravitational anomalies
        self._altitude -= np.random.uniform(0.01, 0.05)
        
        # Inclination drifts due to solar wind and gravitational pull from other bodies
        self._inclination += np.random.uniform(-0.01, 0.01)
        
        # Eccentricity drifts due to various orbital perturbations
        self._eccentricity += np.random.uniform(-0.001, 0.001)

        # Keep parameters within reasonable physical bounds
        self._inclination = np.clip(self._inclination, 0, 180)
        self._eccentricity = np.clip(self._eccentricity, 0, 0.99)


    def apply_orbital_correction(self, correction_vector: List[float]) -> None:
        """
        Applies a correction vector from the PID controller to all orbital parameters.
        Args:
            correction_vector: A 3-element list [alt_corr, inc_corr, ecc_corr].
        """
        if len(correction_vector) == 3:
            self._altitude += correction_vector[0]
            self._inclination += correction_vector[1]
            self._eccentricity += correction_vector[2]

            # Ensure parameters stay within valid ranges after correction
            self._inclination = np.clip(self._inclination, 0, 180)
            self._eccentricity = np.clip(self._eccentricity, 0, 0.99)

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
