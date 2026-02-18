"""Abstract base environment and StepResult dataclass."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    """Result returned by environment.step()."""
    state: Any
    action_taken: str
    reinforced: bool
    schedule_id: str
    done: bool
    reinforcement_magnitude: float = 0.0
    info: dict = field(default_factory=dict)


class AbstractEnvironment(ABC):
    """Base class for all environments."""

    @abstractmethod
    def reset(self) -> Any:
        """Reset environment and return initial state."""
        pass

    @abstractmethod
    def step(self, action: str) -> StepResult:
        """Execute action and return StepResult."""
        pass

    @abstractmethod
    def get_available_actions(self) -> list[str]:
        """Return list of valid action names."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Environment name for display."""
        pass
