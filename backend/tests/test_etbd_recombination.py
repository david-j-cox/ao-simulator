"""Tests for ETBD bitwise recombination."""

import numpy as np
import pytest
from etbd_internals.recombination import recombine, BITS


class TestRecombine:
    def test_identical_parents(self):
        child = recombine(500, 500)
        assert child == 500

    def test_output_in_range(self):
        for _ in range(100):
            child = recombine(
                np.random.randint(0, 1024),
                np.random.randint(0, 1024),
            )
            assert 0 <= child < 1024

    def test_known_crossover_with_seed(self):
        np.random.seed(42)
        child = recombine(0b1111111111, 0b0000000000)
        # With seed 42, crossover_point = np.random.randint(1, 10)
        # The result should be deterministic
        np.random.seed(42)
        child2 = recombine(0b1111111111, 0b0000000000)
        assert child == child2

    def test_crossover_point_range(self):
        # crossover_point is in [1, BITS-1] = [1, 9]
        np.random.seed(0)
        points = set()
        for _ in range(1000):
            point = np.random.randint(1, BITS)
            points.add(point)
        assert min(points) >= 1
        assert max(points) <= BITS - 1

    def test_all_zeros_and_all_ones(self):
        child = recombine(0, 1023)
        assert 0 <= child <= 1023
