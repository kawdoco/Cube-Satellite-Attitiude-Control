"""
control_algorithm.py

Implements the PID controller for satellite station-keeping.
Optimized to use NumPy for efficient vector calculations.
"""
import numpy as np
from typing import List, Tuple

class PIDController:
    """
    A Proportional-Integral-Derivative (PID) controller.

    This controller calculates a correction vector based on the difference
    between a target location and the current location. It uses NumPy for
    fast and efficient vector operations.

    Attributes:
        Kp (float): Proportional gain.
        Ki (float): Integral gain.
        Kd (float): Derivative gain.
    """
    def __init__(self, Kp: float, Ki: float, Kd: float):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        # Internal state vectors, initialized as 3D NumPy arrays
        self._integral = np.zeros(3)
        self._previous_error = np.zeros(3)

    def compute_correction(self,
                           target_location: Tuple[float, float, float],
                           current_location: Tuple[float, float, float]
                           ) -> List[float]:
        """
        Calculates the correction vector using PID logic.

        Args:
            target_location: The desired coordinates (x, y, z).
            current_location: The current measured coordinates (x, y, z).

        Returns:
            The calculated correction vector to be applied by the thrusters.
        """
        # Convert inputs to NumPy arrays for vectorized operations
        target = np.array(target_location)
        current = np.array(current_location)

        # --- PID Calculation ---
        error = target - current
        self._integral += error
        derivative = error - self._previous_error
        self._previous_error = error

        # Calculate the final correction vector
        correction = (self.Kp * error) + (self.Ki * self._integral) + (self.Kd * derivative)

        # Convert back to a list for compatibility with other components
        return correction.tolist()

    def reset(self) -> None:
        """Resets the internal state of the controller."""
        self._integral = np.zeros(3)
        self._previous_error = np.zeros(3)
