"""Tests for SimulationRunner."""

import numpy as np
import pytest
from unittest.mock import MagicMock
from schedules.reinforcement import FR, VI
from environments.two_choice import TwoChoiceEnvironment
from environments.grid_chamber import GridChamberEnvironment
from agents.q_learning import QLearningAgent
from simulation.runner import SimulationRunner


class TestRunnerSingleCondition:
    def test_returns_result(self):
        env = TwoChoiceEnvironment(FR(5), FR(5), max_steps=50)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        result = runner.run(seed=42)
        assert result is not None
        assert result.summary is not None

    def test_step_count_matches(self):
        env = TwoChoiceEnvironment(FR(5), FR(5), max_steps=100)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        result = runner.run(seed=42)
        assert len(result.steps) == 100
        assert result.summary["total_steps"] == 100

    def test_steps_format(self):
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=5)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        result = runner.run(seed=42)
        step = result.steps[0]
        assert "step" in step
        assert "state" in step
        assert "action" in step
        assert "reinforced" in step
        assert "schedule_id" in step
        assert "condition" in step

    def test_seeded_deterministic(self):
        def _run():
            env = TwoChoiceEnvironment(FR(5), FR(5), max_steps=50)
            agent = QLearningAgent()
            runner = SimulationRunner(agent, env)
            return runner.run(seed=123)

        r1 = _run()
        r2 = _run()
        assert [s["action"] for s in r1.steps] == [s["action"] for s in r2.steps]

    def test_resets_agent(self):
        agent = QLearningAgent()
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        runner = SimulationRunner(agent, env)
        runner.run(seed=42)
        # After run, agent was reset at start and used during run.
        # The q_table should have entries from the run.
        assert len(agent.q_table) > 0

    def test_config_contents(self):
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        result = runner.run(seed=42)
        assert result.config["agent"] == "q_learning"
        assert result.config["environment"] == "two_choice"

    def test_reinforcement_rate_math(self):
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        result = runner.run(seed=42)
        expected_rate = result.summary["total_reinforcements"] / result.summary["total_steps"]
        assert result.summary["reinforcement_rate"] == pytest.approx(expected_rate)

    def test_visit_counts_for_grid(self):
        env = GridChamberEnvironment(schedule=FR(1), max_steps=20)
        agent = QLearningAgent(use_history_state=False)
        runner = SimulationRunner(agent, env)
        result = runner.run(seed=42)
        assert "visit_counts" in result.summary


class TestRunnerMultiCondition:
    def _swap(self, env, cond):
        env.max_steps = cond["max_steps"]
        if hasattr(env, "schedule_a"):
            env.schedule_a = FR(cond["schedule_a_value"])
            env.schedule_b = FR(cond["schedule_b_value"])

    def test_basic_two_condition(self):
        env = TwoChoiceEnvironment(FR(5), FR(5), max_steps=50)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        conditions = [
            {"label": "A", "max_steps": 30, "schedule_a_value": 5, "schedule_b_value": 5},
            {"label": "B", "max_steps": 20, "schedule_a_value": 3, "schedule_b_value": 3},
        ]
        result = runner.run_multi_condition(conditions, self._swap, seed=42)
        assert len(result.condition_summaries) == 2
        assert result.summary["total_steps"] == 50

    def test_agent_not_reset_between_conditions(self):
        agent = QLearningAgent()
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        runner = SimulationRunner(agent, env)
        conditions = [
            {"label": "A", "max_steps": 10, "schedule_a_value": 1, "schedule_b_value": 1},
            {"label": "B", "max_steps": 10, "schedule_a_value": 1, "schedule_b_value": 1},
        ]
        result = runner.run_multi_condition(conditions, self._swap, seed=42)
        # Agent should have accumulated history from both conditions
        assert len(agent.history) == 20

    def test_global_step_offset(self):
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        conditions = [
            {"label": "A", "max_steps": 5, "schedule_a_value": 1, "schedule_b_value": 1},
            {"label": "B", "max_steps": 5, "schedule_a_value": 1, "schedule_b_value": 1},
        ]
        result = runner.run_multi_condition(conditions, self._swap, seed=42)
        # Second condition steps should start at 6
        cond2_steps = [s for s in result.steps if s["condition"] == 2]
        assert cond2_steps[0]["step"] == 6

    def test_condition_labels(self):
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        conditions = [
            {"label": "Baseline", "max_steps": 5, "schedule_a_value": 1, "schedule_b_value": 1},
            {"label": "Extinction", "max_steps": 5, "schedule_a_value": 1, "schedule_b_value": 1},
        ]
        result = runner.run_multi_condition(conditions, self._swap, seed=42)
        assert result.condition_summaries[0]["label"] == "Baseline"
        assert result.condition_summaries[1]["label"] == "Extinction"

    def test_swap_env_fn_called(self):
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        swap_mock = MagicMock(side_effect=self._swap)
        conditions = [
            {"label": "A", "max_steps": 5, "schedule_a_value": 1, "schedule_b_value": 1},
            {"label": "B", "max_steps": 5, "schedule_a_value": 1, "schedule_b_value": 1},
        ]
        runner.run_multi_condition(conditions, swap_mock, seed=42)
        assert swap_mock.call_count == 2

    def test_seeded_deterministic(self):
        def _run():
            env = TwoChoiceEnvironment(FR(5), FR(5), max_steps=50)
            agent = QLearningAgent()
            runner = SimulationRunner(agent, env)
            conditions = [
                {"label": "A", "max_steps": 25, "schedule_a_value": 5, "schedule_b_value": 5},
                {"label": "B", "max_steps": 25, "schedule_a_value": 3, "schedule_b_value": 3},
            ]
            return runner.run_multi_condition(conditions, self._swap, seed=99)

        r1 = _run()
        r2 = _run()
        assert [s["action"] for s in r1.steps] == [s["action"] for s in r2.steps]

    def test_summary_aggregates(self):
        env = TwoChoiceEnvironment(FR(1), FR(1), max_steps=10)
        agent = QLearningAgent()
        runner = SimulationRunner(agent, env)
        conditions = [
            {"label": "A", "max_steps": 10, "schedule_a_value": 1, "schedule_b_value": 1},
            {"label": "B", "max_steps": 10, "schedule_a_value": 1, "schedule_b_value": 1},
        ]
        result = runner.run_multi_condition(conditions, self._swap, seed=42)
        total = sum(cs["total_steps"] for cs in result.condition_summaries)
        assert result.summary["total_steps"] == total
