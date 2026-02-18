"""ETBD (Evolutionary Theory of Behavior Dynamics) agent."""

import numpy as np
from typing import Any
from agents.base import AbstractAgent
from etbd_internals.organism import Organism


# Response class mappings
TWO_CHOICE_MAP = {
    "choice_a": (0, 512),
    "choice_b": (512, 1024),
}

GRID_MAP = {
    "up": (0, 171),
    "down": (171, 342),
    "left": (342, 513),
    "right": (513, 684),
    "stay": (684, 855),
    "press_lever": (855, 1024),
}


def phenotype_to_action(phenotype: int, action_map: dict[str, tuple[int, int]]) -> str:
    """Convert a phenotype integer to an action name based on the mapping."""
    for action, (low, high) in action_map.items():
        if low <= phenotype < high:
            return action
    # Fallback (shouldn't happen with proper ranges)
    return list(action_map.keys())[0]


def action_to_target(action: str, action_map: dict[str, tuple[int, int]]) -> int:
    """Get the midpoint phenotype for a given action class."""
    low, high = action_map[action]
    return (low + high) // 2


class ETBDAgent(AbstractAgent):
    """ETBD agent using a genetic algorithm to model operant behavior.

    Uses the Organism class internally. Response class mapping depends
    on the environment (two-choice vs grid).
    """

    def __init__(
        self,
        population_size: int = 100,
        mutation_rate: float = 0.1,
        fitness_decay: float = 0.95,
        environment_type: str = "two_choice",
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.fitness_decay = fitness_decay
        self.environment_type = environment_type

        if environment_type == "grid_chamber":
            self.action_map = GRID_MAP
        else:
            self.action_map = TWO_CHOICE_MAP

        self.organism = Organism(
            population_size=population_size,
            mutation_rate=mutation_rate,
            fitness_decay=fitness_decay,
        )

    def select_action(self, state: Any, available_actions: list[str]) -> str:
        phenotype = self.organism.emit()
        action = phenotype_to_action(phenotype, self.action_map)
        return action

    def update(self, state: Any, action: str, reinforced: bool, next_state: Any, magnitude: float = 1.0):
        if reinforced and magnitude > 0:
            target = action_to_target(action, self.action_map)
            self.organism.reinforce(target)
        else:
            self.organism.drift()

    def reset(self):
        self.organism.reset()

    def get_params(self) -> dict:
        return {
            "population_size": self.population_size,
            "mutation_rate": self.mutation_rate,
            "fitness_decay": self.fitness_decay,
            "environment_type": self.environment_type,
        }

    @property
    def name(self) -> str:
        return "etbd"
