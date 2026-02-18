"""Tests for MPR agent."""

import numpy as np
import pytest
from agents.mpr import MPRAgent


class TestMPRAgent:
    def test_coupling_floor_at_start(self):
        agent = MPRAgent(coupling_floor=0.01)
        c = agent._get_coupling("a")
        assert c == 0.01

    def test_coupling_floor_when_no_counts(self):
        agent = MPRAgent(coupling_floor=0.05)
        agent.total_steps = 10
        c = agent._get_coupling("a")
        assert c == 0.05

    def test_ratio_formula(self):
        agent = MPRAgent(
            initial_arousal=1.0,
            activation_decay=0.5,
            coupling_floor=0.0,
            schedule_type="FR",
        )
        agent.total_steps = 10
        agent.action_counts["a"] = 10
        agent.reinforcement_counts["a"] = 5
        R = 5 / 10  # 0.5
        expected = 1.0 * np.exp(-0.5 / 0.5)
        assert agent._get_coupling("a") == pytest.approx(expected)

    def test_interval_formula(self):
        agent = MPRAgent(
            initial_arousal=2.0,
            activation_decay=0.5,
            coupling_floor=0.0,
            schedule_type="VI",
        )
        agent.total_steps = 10
        agent.action_counts["a"] = 10
        agent.reinforcement_counts["a"] = 2
        R = 2 / 10  # 0.2
        expected = 2.0 * 0.2 / (0.2 + 0.5)
        assert agent._get_coupling("a") == pytest.approx(expected)

    def test_never_below_floor(self):
        agent = MPRAgent(coupling_floor=0.5, schedule_type="VI")
        agent.total_steps = 100
        agent.action_counts["a"] = 100
        agent.reinforcement_counts["a"] = 0
        assert agent._get_coupling("a") >= 0.5

    def test_two_choice_matching_law(self):
        agent = MPRAgent(environment_type="two_choice", coupling_floor=0.01)
        # Both at floor → ~50/50
        counts = {"choice_a": 0, "choice_b": 0}
        for _ in range(2000):
            a = agent.select_action("s", ["choice_a", "choice_b"])
            counts[a] += 1
        assert abs(counts["choice_a"] - counts["choice_b"]) < 300

    def test_grid_softmax(self):
        agent = MPRAgent(environment_type="grid_chamber", coupling_floor=0.01)
        actions = ["up", "down", "left", "right", "stay", "press_lever"]
        action = agent.select_action((0, 0), actions)
        assert action in actions

    def test_update_increments_counts(self):
        agent = MPRAgent()
        agent.update("s", "a", True, "s2")
        assert agent.action_counts["a"] == 1
        assert agent.reinforcement_counts["a"] == 1
        assert agent.total_steps == 1

    def test_update_no_reinforcement(self):
        agent = MPRAgent()
        agent.update("s", "a", False, "s2")
        assert agent.action_counts["a"] == 1
        assert agent.reinforcement_counts.get("a", 0) == 0

    def test_reset(self):
        agent = MPRAgent()
        agent.update("s", "a", True, "s2")
        agent.reset()
        assert agent.action_counts == {}
        assert agent.reinforcement_counts == {}
        assert agent.total_steps == 0

    def test_name(self):
        assert MPRAgent().name == "mpr"

    def test_get_params(self):
        agent = MPRAgent(initial_arousal=2.0, temperature=0.5)
        p = agent.get_params()
        assert p["initial_arousal"] == 2.0
        assert p["temperature"] == 0.5

    def test_case_insensitive_schedule_type(self):
        agent = MPRAgent(schedule_type="vi")
        assert agent.schedule_type == "VI"
