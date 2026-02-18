"""Tests for Q-Learning agent."""

import numpy as np
import pytest
from agents.q_learning import QLearningAgent


class TestQLearningAgent:
    def test_initial_q_zero(self):
        agent = QLearningAgent()
        state_key = agent._get_state_key("start")
        assert agent.q_table[state_key]["choice_a"] == 0.0

    def test_random_when_no_q(self):
        agent = QLearningAgent(epsilon=0.0)
        actions = ["a", "b"]
        counts = {"a": 0, "b": 0}
        for _ in range(1000):
            a = agent.select_action("start", actions)
            counts[a] += 1
        # With epsilon=0 but no Q values, picks randomly
        assert counts["a"] > 100
        assert counts["b"] > 100

    def test_epsilon_0_exploits(self):
        agent = QLearningAgent(epsilon=0.0)
        # Manually set Q value
        state_key = agent._get_state_key("start")
        agent.q_table[state_key]["a"] = 10.0
        agent.q_table[state_key]["b"] = 1.0
        for _ in range(50):
            assert agent.select_action("start", ["a", "b"]) == "a"

    def test_epsilon_1_explores(self):
        agent = QLearningAgent(epsilon=1.0)
        state_key = agent._get_state_key("start")
        agent.q_table[state_key]["a"] = 100.0
        agent.q_table[state_key]["b"] = 0.0
        counts = {"a": 0, "b": 0}
        for _ in range(1000):
            a = agent.select_action("start", ["a", "b"])
            counts[a] += 1
        assert counts["b"] > 300  # should be ~50%

    def test_update_increases_q_on_reward(self):
        # use_history_state=False so state key is stable
        agent = QLearningAgent(alpha=0.1, gamma=0.9, use_history_state=False)
        state_key = agent._get_state_key("start")
        old_q = agent.q_table[state_key]["a"]
        agent.update("start", "a", True, "start")
        new_q = agent.q_table[state_key]["a"]
        assert new_q > old_q

    def test_update_formula_with_existing_q(self):
        # use_history_state=False so state key is stable
        agent = QLearningAgent(alpha=0.5, gamma=0.0, use_history_state=False)
        state_key = agent._get_state_key("s")
        agent.q_table[state_key]["a"] = 2.0
        # reward=1, gamma=0 → new_q = 2.0 + 0.5*(1 + 0 - 2.0) = 2.0 + 0.5*(-1) = 1.5
        agent.update("s", "a", True, "s2")
        assert agent.q_table[state_key]["a"] == pytest.approx(1.5)

    def test_history_state_builds_correctly(self):
        agent = QLearningAgent(history_window=3, use_history_state=True)
        agent.history = ["a", "b", "c", "d"]
        key = agent._get_state_key("ignored")
        assert key == ("b", "c", "d")

    def test_short_history(self):
        agent = QLearningAgent(history_window=3, use_history_state=True)
        agent.history = ["a"]
        key = agent._get_state_key("ignored")
        assert key == ("a",)

    def test_grid_state_uses_position(self):
        agent = QLearningAgent(use_history_state=False)
        key = agent._get_state_key((2, 3))
        assert key == (2, 3)

    def test_reset_clears(self):
        agent = QLearningAgent()
        agent.update("s", "a", True, "s2")
        agent.reset()
        assert len(agent.q_table) == 0
        assert len(agent.history) == 0

    def test_name(self):
        assert QLearningAgent().name == "q_learning"

    def test_get_params(self):
        agent = QLearningAgent(alpha=0.2, gamma=0.8, epsilon=0.3, history_window=5)
        p = agent.get_params()
        assert p["alpha"] == 0.2
        assert p["gamma"] == 0.8
        assert p["epsilon"] == 0.3
        assert p["history_window"] == 5
        assert "q_table_size" in p
