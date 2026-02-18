"""Tests for ETBD circular fitness landscape."""

import math
import pytest
from etbd_internals.fitness import circular_distance, fitness_value


class TestCircularDistance:
    def test_same_value(self):
        assert circular_distance(100, 100) == 0

    def test_direct_distance(self):
        assert circular_distance(0, 10) == 10

    def test_wraps_around(self):
        # 0 and 1020: direct = 1020, wrap = 1024-1020 = 4
        assert circular_distance(0, 1020) == 4

    def test_symmetric(self):
        assert circular_distance(200, 800) == circular_distance(800, 200)

    def test_max_distance_is_half(self):
        assert circular_distance(0, 512) == 512
        assert circular_distance(0, 513) == 511  # wraps


class TestFitnessValue:
    def test_at_target_equals_1(self):
        assert fitness_value(500, 500) == pytest.approx(1.0)

    def test_distance_1(self):
        assert fitness_value(500, 501) == pytest.approx(0.95)

    def test_far_away(self):
        val = fitness_value(0, 512)
        assert val < 0.01  # 0.95^512 is very small

    def test_custom_decay(self):
        val = fitness_value(0, 1, decay=0.5)
        assert val == pytest.approx(0.5)

    def test_wrapping_fitness(self):
        # 0 and 1020: distance = 4
        expected = 0.95 ** 4
        assert fitness_value(0, 1020) == pytest.approx(expected)
