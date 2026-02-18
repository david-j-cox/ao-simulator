"""Tests for ETBD bit-flip mutation."""

import numpy as np
import pytest
from etbd_internals.mutation import mutate, BITS


class TestMutate:
    def test_rate_0_no_change(self):
        for val in [0, 500, 1023]:
            assert mutate(val, mutation_rate=0.0) == val

    def test_rate_1_all_flip(self):
        result = mutate(0b0000000000, mutation_rate=1.0)
        assert result == 0b1111111111

    def test_output_in_range(self):
        for _ in range(200):
            val = np.random.randint(0, 1024)
            result = mutate(val, 0.5)
            assert 0 <= result < 1024

    def test_seeded_deterministic(self):
        np.random.seed(42)
        r1 = mutate(500, 0.1)
        np.random.seed(42)
        r2 = mutate(500, 0.1)
        assert r1 == r2

    def test_statistical_bit_flip_rate(self):
        np.random.seed(42)
        flips = 0
        trials = 5000
        for _ in range(trials):
            original = 0
            result = mutate(original, mutation_rate=0.5)
            flips += bin(result).count("1")
        rate = flips / (trials * BITS)
        assert 0.45 < rate < 0.55
