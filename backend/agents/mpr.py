"""MPR (Mathematical Principles of Reinforcement) agent."""

import numpy as np
from typing import Any
from agents.base import AbstractAgent


class MPRAgent(AbstractAgent):
    """MPR-based agent implementing Killeen's mathematical principles of reinforcement.

    Two-choice: P(A) = C_A / (C_A + C_B) matching law concurrent choice.
    Grid (6 actions): softmax over coupling values.

    Coupling (C*) formula depends on schedule type:
    - FR/VR (ratio): C = a * exp(-b / R)  (exponential)
    - FI/VI (interval): C = a * R / (R + b) (hyperbolic)

    Where R is reinforcement rate, a is specific activation, b is arousal.
    """

    def __init__(
        self,
        environment_type: str = "two_choice",
        initial_arousal: float = 1.0,
        activation_decay: float = 0.95,
        coupling_floor: float = 0.01,
        learning_rate: float = 0.1,
        schedule_type: str = "VI",
        temperature: float = 1.0,
    ):
        self.environment_type = environment_type
        self.initial_arousal = initial_arousal
        self.activation_decay = activation_decay
        self.coupling_floor = coupling_floor
        self.learning_rate = learning_rate
        self.schedule_type = schedule_type.upper()
        self.temperature = temperature

        # Track per-action stats
        self.action_counts: dict[str, int] = {}
        self.reinforcement_counts: dict[str, int] = {}
        self.total_steps = 0

    def _get_coupling(self, action: str) -> float:
        """Compute coupling value C* for an action based on its reinforcement rate."""
        if self.total_steps == 0:
            return self.coupling_floor

        action_count = self.action_counts.get(action, 0)
        reinf_count = self.reinforcement_counts.get(action, 0)

        if action_count == 0:
            return self.coupling_floor

        # Reinforcement rate = reinforcements per response
        R = reinf_count / action_count

        a = self.initial_arousal
        b = self.activation_decay

        if self.schedule_type in ("FR", "VR"):
            # Exponential coupling
            C = a * np.exp(-b / max(R, 1e-10))
        else:
            # Hyperbolic coupling (FI, VI)
            C = a * R / (R + b)

        return max(C, self.coupling_floor)

    def select_action(self, state: Any, available_actions: list[str]) -> str:
        couplings = {a: self._get_coupling(a) for a in available_actions}

        if self.environment_type == "two_choice" and len(available_actions) == 2:
            # Matching law: P(A) = C_A / (C_A + C_B)
            a, b = available_actions
            total = couplings[a] + couplings[b]
            p_a = couplings[a] / total
            return a if np.random.random() < p_a else b
        else:
            # Softmax over couplings for grid
            values = np.array([couplings[a] for a in available_actions])
            scaled = values / self.temperature
            scaled -= scaled.max()  # numerical stability
            exp_vals = np.exp(scaled)
            probs = exp_vals / exp_vals.sum()
            idx = np.random.choice(len(available_actions), p=probs)
            return available_actions[idx]

    def update(self, state: Any, action: str, reinforced: bool, next_state: Any, magnitude: float = 1.0):
        self.total_steps += 1
        self.action_counts[action] = self.action_counts.get(action, 0) + 1
        if reinforced and magnitude > 0:
            self.reinforcement_counts[action] = self.reinforcement_counts.get(action, 0) + 1

    def reset(self):
        self.action_counts = {}
        self.reinforcement_counts = {}
        self.total_steps = 0

    def get_params(self) -> dict:
        return {
            "environment_type": self.environment_type,
            "initial_arousal": self.initial_arousal,
            "activation_decay": self.activation_decay,
            "coupling_floor": self.coupling_floor,
            "schedule_type": self.schedule_type,
            "temperature": self.temperature,
        }

    @property
    def name(self) -> str:
        return "mpr"
