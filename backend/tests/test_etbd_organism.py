"""Tests for ETBD Organism class."""

import numpy as np
import pytest
from etbd_internals.organism import Organism


class TestOrganism:
    def test_init_size(self):
        o = Organism(population_size=50)
        assert len(o.population) == 50

    def test_phenotype_range(self):
        o = Organism(population_size=200)
        for p in o.population:
            assert 0 <= p < 1024

    def test_emit_returns_member(self):
        o = Organism(population_size=20)
        for _ in range(50):
            val = o.emit()
            assert val in o.population

    def test_reinforce_changes_population(self):
        o = Organism(population_size=50)
        old_pop = list(o.population)
        o.reinforce(target=512)
        assert o.population != old_pop

    def test_reinforce_preserves_size(self):
        o = Organism(population_size=50)
        o.reinforce(target=512)
        assert len(o.population) == 50

    def test_reinforce_shifts_toward_target(self):
        o = Organism(population_size=100, mutation_rate=0.01, fitness_decay=0.99)
        target = 512
        for _ in range(50):
            o.reinforce(target)
        mean = np.mean(o.population)
        assert abs(mean - target) < 200  # should converge roughly

    def test_drift_changes_population(self):
        o = Organism(population_size=50)
        old_pop = list(o.population)
        o.drift()
        assert o.population != old_pop

    def test_drift_preserves_size(self):
        o = Organism(population_size=50)
        o.drift()
        assert len(o.population) == 50

    def test_drift_no_directional_shift(self):
        np.random.seed(42)
        o = Organism(population_size=200, mutation_rate=0.01)
        mean_before = np.mean(o.population)
        for _ in range(10):
            o.drift()
        mean_after = np.mean(o.population)
        # No strong directional pressure
        assert abs(mean_after - mean_before) < 200

    def test_reset_repopulates(self):
        o = Organism(population_size=50)
        for _ in range(10):
            o.reinforce(0)
        o.reset()
        assert len(o.population) == 50
        # New random population, should not all be near 0
        assert np.mean(o.population) > 100
