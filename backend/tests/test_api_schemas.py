"""Tests for Pydantic API schemas."""

import pytest
from pydantic import ValidationError
from api.schemas import (
    ScheduleConfig, QLearningParams, ETBDParams, MPRParams,
    GridConfig, SimulationRequest, ConditionConfig,
)


class TestScheduleConfig:
    def test_valid(self):
        s = ScheduleConfig(type="FR", value=5)
        assert s.type == "FR"
        assert s.value == 5

    def test_value_must_be_positive(self):
        with pytest.raises(ValidationError):
            ScheduleConfig(type="FR", value=0)

    def test_negative_value_invalid(self):
        with pytest.raises(ValidationError):
            ScheduleConfig(type="VI", value=-1)


class TestQLearningParams:
    def test_defaults(self):
        p = QLearningParams()
        assert p.alpha == 0.1
        assert p.gamma == 0.9
        assert p.epsilon == 0.1
        assert p.history_window == 3

    def test_bounds(self):
        with pytest.raises(ValidationError):
            QLearningParams(alpha=1.5)
        with pytest.raises(ValidationError):
            QLearningParams(history_window=0)


class TestETBDParams:
    def test_defaults(self):
        p = ETBDParams()
        assert p.population_size == 100
        assert p.mutation_rate == 0.1
        assert p.fitness_decay == 0.95

    def test_bounds(self):
        with pytest.raises(ValidationError):
            ETBDParams(population_size=5)  # min 10
        with pytest.raises(ValidationError):
            ETBDParams(mutation_rate=1.5)


class TestMPRParams:
    def test_defaults(self):
        p = MPRParams()
        assert p.initial_arousal == 1.0
        assert p.temperature == 1.0

    def test_bounds(self):
        with pytest.raises(ValidationError):
            MPRParams(initial_arousal=0)  # gt=0
        with pytest.raises(ValidationError):
            MPRParams(coupling_floor=-0.1)


class TestGridConfig:
    def test_defaults(self):
        g = GridConfig()
        assert g.rows == 5
        assert g.cols == 5

    def test_bounds(self):
        with pytest.raises(ValidationError):
            GridConfig(rows=1)  # min 2
        with pytest.raises(ValidationError):
            GridConfig(cols=25)  # max 20


class TestSimulationRequest:
    def test_minimal(self):
        r = SimulationRequest(environment="two_choice", algorithm="q_learning")
        assert r.max_steps == 1000
        assert r.seed is None

    def test_bounds(self):
        with pytest.raises(ValidationError):
            SimulationRequest(environment="two_choice", algorithm="q_learning", max_steps=0)


class TestConditionConfig:
    def test_requires_label(self):
        with pytest.raises(ValidationError):
            ConditionConfig(max_steps=100)

    def test_max_6_conditions(self):
        conds = [ConditionConfig(label=f"C{i}", max_steps=10) for i in range(7)]
        with pytest.raises(ValidationError):
            SimulationRequest(
                environment="two_choice",
                algorithm="q_learning",
                conditions=conds,
            )
