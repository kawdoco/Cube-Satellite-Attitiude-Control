"""
telemetry.py

Manages logging of real-time satellite telemetry data.
Optimized to use a deque with a fixed size to prevent infinite memory growth.
"""
import datetime
import numpy as np
from collections import deque
from typing import Tuple, List, Optional

class TelemetrySystem:
    """
    Manages telemetry logging using a fixed-size deque for efficiency.
    """
    def __init__(self, max_log_size: int):
        # A deque automatically discards old entries when the max size is reached.
        self._telemetry_log = deque(maxlen=max_log_size)

    def log_status(self,
                   timestamp: datetime.datetime,
                   current_location: Tuple[float, float, float],
                   target_location: Tuple[float, float, float],
                   correction_vector: Optional[List[float]],
                   is_on_course: bool) -> None:
        """
        Records a new telemetry entry.

        Args:
            timestamp: The timestamp of the log entry.
            current_location: The satellite's current position.
            target_location: The satellite's target position.
            correction_vector: The thrust vector applied, if any.
            is_on_course: Boolean indicating if the satellite is within tolerance.
        """
        current_loc_np = np.array(current_location)
        target_loc_np = np.array(target_location)

        # Calculate error magnitude using NumPy for efficiency
        error_magnitude = np.linalg.norm(target_loc_np - current_loc_np)

        entry = {
            "timestamp": timestamp,
            "current_location": current_location,
            "target_location": target_location,
            "error_magnitude": error_magnitude,
            "correction_vector": correction_vector,
            "is_on_course": is_on_course
        }
        self._telemetry_log.append(entry)

    def get_latest_log(self) -> Optional[dict]:
        """Returns the most recent telemetry entry, or None if empty."""
        return self._telemetry_log[-1] if self._telemetry_log else None
