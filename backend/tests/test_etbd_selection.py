"""Tests for ETBD fitness-proportionate selection."""

import numpy as np
import pytest
from etbd_internals.selection import select_parent


class TestSelectParent:
    def test_single_element(self):
        result = select_parent([500], target=500)
        assert result == 500

    def test_favors_close_to_target(self):
        pop = [0, 500, 1000]
        counts = {0: 0, 500: 0, 1000: 0}
        for _ in range(1000):
            p = select_parent(pop, target=500)
            counts[p] += 1
        # 500 is at target → should be selected most often
        assert counts[500] > counts[0]
        assert counts[500] > counts[1000]

    def test_uniform_when_equidistant(self):
        # 256 and 768 are equidistant from 512
        pop = [256, 768]
        counts = {256: 0, 768: 0}
        for _ in range(2000):
            p = select_parent(pop, target=512)
            counts[p] += 1
        # Should be roughly 50/50
        assert abs(counts[256] - counts[768]) < 300

    def test_returns_population_member(self):
        pop = [10, 20, 30]
        result = select_parent(pop, target=20)
        assert result in pop

    def test_zero_fitness_fallback(self):
        # decay=0 makes all fitness 0 except exact target
        pop = [100, 200, 300]
        result = select_parent(pop, target=500, decay=0.0)
        assert result in pop
