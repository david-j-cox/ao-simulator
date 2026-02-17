"""Reinforcement schedule classes: FR, VR, FI, VI."""

import numpy as np
from abc import ABC, abstractmethod


class Schedule(ABC):
    """Base reinforcement schedule."""

    def __init__(self, value: int):
        self.value = value
        self.reset()

    @abstractmethod
    def reset(self):
        """Reset internal counters."""
        pass

    @abstractmethod
    def check(self, is_target_response: bool) -> bool:
        """Return True if reinforcement should be delivered.

        Args:
            is_target_response: Whether the response was an in-class (target) response.
        """
        pass

    @abstractmethod
    def tick(self):
        """Advance one time step (for interval schedules)."""
        pass


class FR(Schedule):
    """Fixed-Ratio: reinforce every N-th in-class response."""

    def reset(self):
        self.count = 0

    def check(self, is_target_response: bool) -> bool:
        if not is_target_response:
            return False
        self.count += 1
        if self.count >= self.value:
            self.count = 0
            return True
        return False

    def tick(self):
        pass


class VR(Schedule):
    """Variable-Ratio: reinforce after geometrically-distributed count of in-class responses."""

    def reset(self):
        self._set_next_ratio()
        self.count = 0

    def _set_next_ratio(self):
        # Exponential distribution with mean = self.value, rounded to at least 1
        self.next_ratio = max(1, int(np.random.exponential(self.value)))

    def check(self, is_target_response: bool) -> bool:
        if not is_target_response:
            return False
        self.count += 1
        if self.count >= self.next_ratio:
            self.count = 0
            self._set_next_ratio()
            return True
        return False

    def tick(self):
        pass


class FI(Schedule):
    """Fixed-Interval: reinforce first in-class response after N steps elapsed."""

    def reset(self):
        self.elapsed = 0
        self.armed = False

    def check(self, is_target_response: bool) -> bool:
        if self.armed and is_target_response:
            self.armed = False
            self.elapsed = 0
            return True
        return False

    def tick(self):
        self.elapsed += 1
        if self.elapsed >= self.value:
            self.armed = True


class VI(Schedule):
    """Variable-Interval: reinforce first in-class response after exponentially-distributed interval."""

    def reset(self):
        self.elapsed = 0
        self.armed = False
        self._set_next_interval()

    def _set_next_interval(self):
        self.next_interval = max(1, int(np.random.exponential(self.value)))

    def check(self, is_target_response: bool) -> bool:
        if self.armed and is_target_response:
            self.armed = False
            self.elapsed = 0
            self._set_next_interval()
            return True
        return False

    def tick(self):
        self.elapsed += 1
        if self.elapsed >= self.next_interval:
            self.armed = True


def create_schedule(schedule_type: str, value: int) -> Schedule:
    """Factory function to create a schedule by type name."""
    schedules = {
        "FR": FR,
        "VR": VR,
        "FI": FI,
        "VI": VI,
    }
    cls = schedules.get(schedule_type.upper())
    if cls is None:
        raise ValueError(f"Unknown schedule type: {schedule_type}. Must be one of {list(schedules.keys())}")
    return cls(value)
