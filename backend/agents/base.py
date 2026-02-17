"""Abstract base agent."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractAgent(ABC):
    """Base class for all agents."""

    @abstractmethod
    def select_action(self, state: Any, available_actions: list[str]) -> str:
        """Choose an action given state and available actions."""
        pass

    @abstractmethod
    def update(self, state: Any, action: str, reinforced: bool, next_state: Any):
        """Update agent after observing outcome."""
        pass

    @abstractmethod
    def reset(self):
        """Reset agent to initial state."""
        pass

    @abstractmethod
    def get_params(self) -> dict:
        """Return current parameters for logging."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for display."""
        pass
