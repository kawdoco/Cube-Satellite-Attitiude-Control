"""
satellite_components.py

Defines the physical components of the satellite.
Optimized to use NumPy for efficient location and vector calculations.
"""
import numpy as np
from typing import List, Tuple

class Satellite:
    """
    Represents an autonomous satellite.
    Uses NumPy arrays to store location for efficient vector math.
    """
    def __init__(self, target_location: Tuple[float, float, float]):
        self._target_location = np.array(target_location, dtype=float)
        self._current_location = np.array(target_location, dtype=float)

    def get_location(self) -> np.ndarray:
        """Returns the current location as a NumPy array."""
        return self._current_location

    def set_location(self, new_coordinates: np.ndarray) -> None:
        """Sets the current location from a NumPy array."""
        self._current_location = new_coordinates

    def simulate_drift(self) -> None:
        """Simulates gradual orbital drift by applying a random vector."""
        # Generate a random 3D drift vector
        drift_vector = np.random.uniform(-0.05, 0.05, 3)
        self._current_location += drift_vector

class Thruster:
    """Represents the satellite's propulsion system."""
    def apply_thrust(self, satellite: Satellite, correction_vector: List[float]) -> np.ndarray:
        """
        Applies a thrust to the satellite.

        Args:
            satellite: The satellite object to modify.
            correction_vector: The vector to apply.

        Returns:
            The new location of the satellite.
        """
        current_location = satellite.get_location()
        correction = np.array(correction_vector)
        new_location = current_location + correction
        satellite.set_location(new_location)
        return new_location

class Sensor:
    """Simulates a sensor that provides the satellite's current position."""
    def __init__(self, satellite: Satellite):
        self._satellite = satellite

    def get_current_position(self) -> Tuple[float, float, float]:
        """
        Returns the satellite's current position.
        Introduces a small amount of simulated sensor noise.
        """
        # Get true location
        true_location = self._satellite.get_location()
        # Add a small random noise to simulate sensor inaccuracy
        noise = np.random.normal(0, 0.01, 3)
        sensed_location = true_location + noise
        return tuple(sensed_location)
