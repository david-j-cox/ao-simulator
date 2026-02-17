"""Q-Learning agent."""

import numpy as np
from collections import defaultdict
from typing import Any
from agents.base import AbstractAgent


class QLearningAgent(AbstractAgent):
    """Tabular Q-Learning agent.

    For two-choice: state = tuple of last N choices (configurable window).
    For grid: state = (row, col).
    Epsilon-greedy action selection.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        gamma: float = 0.9,
        epsilon: float = 0.1,
        history_window: int = 3,
        use_history_state: bool = True,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.history_window = history_window
        self.use_history_state = use_history_state
        self.q_table: dict[Any, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.history: list[str] = []

    def _get_state_key(self, state: Any) -> Any:
        if self.use_history_state:
            return tuple(self.history[-self.history_window:])
        if isinstance(state, list):
            return tuple(state)
        return state

    def select_action(self, state: Any, available_actions: list[str]) -> str:
        state_key = self._get_state_key(state)

        if np.random.random() < self.epsilon:
            return np.random.choice(available_actions)

        q_values = self.q_table[state_key]
        if not q_values:
            return np.random.choice(available_actions)

        max_q = max(q_values.get(a, 0.0) for a in available_actions)
        best_actions = [a for a in available_actions if q_values.get(a, 0.0) == max_q]
        return np.random.choice(best_actions)

    def update(self, state: Any, action: str, reinforced: bool, next_state: Any):
        self.history.append(action)
        state_key = self._get_state_key(state)
        next_state_key = self._get_state_key(next_state)

        reward = 1.0 if reinforced else 0.0
        next_q_values = self.q_table[next_state_key]
        max_next_q = max(next_q_values.values()) if next_q_values else 0.0

        current_q = self.q_table[state_key][action]
        self.q_table[state_key][action] = current_q + self.alpha * (
            reward + self.gamma * max_next_q - current_q
        )

    def reset(self):
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.history = []

    def get_params(self) -> dict:
        return {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "history_window": self.history_window,
            "q_table_size": len(self.q_table),
        }

    @property
    def name(self) -> str:
        return "q_learning"
