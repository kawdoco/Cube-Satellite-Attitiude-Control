"""
history.py

Records and manages the history of satellite drift and correction events.
Optimized to use a deque with a fixed size to prevent infinite memory growth.
"""
import datetime
from collections import deque
from typing import Tuple, List, Optional

class HistoryRecorder:
    """
    Records drift events using a fixed-size deque for memory efficiency.
    """
    def __init__(self, max_history_size: int):
        self._drift_history = deque(maxlen=max_history_size)

    def record_drift(self,
                     timestamp: datetime.datetime,
                     location: Tuple[float, float, float],
                     error_magnitude: float,
                     correction_vector: List[float]) -> None:
        """
        Records an event where the satellite drifted and was corrected.
        """
        drift_event = {
            "timestamp": timestamp,
            "location": location,
            "error_magnitude": error_magnitude,
            "correction_vector": correction_vector
        }
        self._drift_history.append(drift_event)

    def get_drift_history(self) -> deque:
        """Returns the deque of recorded drift events."""
        return self._drift_history

    def clear_history(self) -> None:
        """Clears the recorded drift history."""
        self._drift_history.clear()
