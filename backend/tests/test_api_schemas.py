"""Tests for Pydantic API schemas."""

import pytest
from pydantic import ValidationError
from api.schemas import (
    ScheduleConfig, QLearningParams, ETBDParams, MPRParams,
    GridConfig, SimulationRequest, ConditionConfig,
    LeverConfig, LeverScheduleConfig,
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


class TestLeverConfig:
    def test_valid(self):
        lc = LeverConfig(row=2, col=3, schedule=ScheduleConfig(type="FR", value=5))
        assert lc.row == 2
        assert lc.col == 3
        assert lc.magnitude == 1.0

    def test_custom_magnitude(self):
        lc = LeverConfig(row=0, col=0, schedule=ScheduleConfig(type="VI", value=10), magnitude=2.5)
        assert lc.magnitude == 2.5

    def test_zero_magnitude(self):
        lc = LeverConfig(row=0, col=0, schedule=ScheduleConfig(type="FR", value=1), magnitude=0.0)
        assert lc.magnitude == 0.0

    def test_negative_magnitude_invalid(self):
        with pytest.raises(ValidationError):
            LeverConfig(row=0, col=0, schedule=ScheduleConfig(type="FR", value=1), magnitude=-1.0)

    def test_negative_row_invalid(self):
        with pytest.raises(ValidationError):
            LeverConfig(row=-1, col=0, schedule=ScheduleConfig(type="FR", value=1))


class TestLeverScheduleConfig:
    def test_valid(self):
        ls = LeverScheduleConfig(schedule=ScheduleConfig(type="VI", value=30), magnitude=1.5)
        assert ls.schedule.type == "VI"
        assert ls.magnitude == 1.5

    def test_defaults(self):
        ls = LeverScheduleConfig(schedule=ScheduleConfig(type="FR", value=5))
        assert ls.magnitude == 1.0

    def test_zero_magnitude(self):
        ls = LeverScheduleConfig(schedule=ScheduleConfig(type="FR", value=5), magnitude=0.0)
        assert ls.magnitude == 0.0


class TestGridConfig:
    def test_defaults(self):
        g = GridConfig()
        assert g.rows == 5
        assert g.cols == 5
        assert len(g.levers) == 1
        assert g.levers[0].row == 2
        assert g.levers[0].col == 2

    def test_bounds(self):
        with pytest.raises(ValidationError):
            GridConfig(rows=1)  # min 2
        with pytest.raises(ValidationError):
            GridConfig(cols=25)  # max 20

    def test_multiple_levers(self):
        levers = [
            LeverConfig(row=1, col=1, schedule=ScheduleConfig(type="FR", value=5)),
            LeverConfig(row=3, col=3, schedule=ScheduleConfig(type="VI", value=10), magnitude=2.0),
        ]
        g = GridConfig(levers=levers)
        assert len(g.levers) == 2
        assert g.levers[1].magnitude == 2.0

    def test_max_8_levers(self):
        levers = [
            LeverConfig(row=i, col=0, schedule=ScheduleConfig(type="FR", value=1))
            for i in range(9)
        ]
        with pytest.raises(ValidationError):
            GridConfig(levers=levers)

    def test_min_1_lever(self):
        with pytest.raises(ValidationError):
            GridConfig(levers=[])


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

    def test_lever_schedules(self):
        c = ConditionConfig(
            label="Test",
            lever_schedules=[
                LeverScheduleConfig(schedule=ScheduleConfig(type="FR", value=5), magnitude=1.0),
                LeverScheduleConfig(schedule=ScheduleConfig(type="VI", value=10), magnitude=0.0),
            ],
        )
        assert len(c.lever_schedules) == 2
        assert c.lever_schedules[1].magnitude == 0.0
