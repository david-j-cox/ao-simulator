"""Circular fitness landscape for ETBD."""

import numpy as np


def circular_distance(a: int, b: int, max_val: int = 1024) -> int:
    """Compute circular distance between two phenotype values."""
    diff = abs(a - b)
    return min(diff, max_val - diff)


def fitness_value(phenotype: int, target: int, max_val: int = 1024, decay: float = 0.95) -> float:
    """Compute fitness of a phenotype given a target.

    Uses exponential decay based on circular distance.
    """
    dist = circular_distance(phenotype, target, max_val)
    return decay ** dist
