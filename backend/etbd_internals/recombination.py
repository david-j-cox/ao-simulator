"""Bitwise recombination for ETBD."""

import numpy as np

BITS = 10


def recombine(parent_a: int, parent_b: int) -> int:
    """Single-point crossover between two phenotypes.

    A random crossover point is selected. Bits below the crossover point
    come from parent_a, bits at or above come from parent_b.
    """
    crossover_point = np.random.randint(1, BITS)
    mask = (1 << crossover_point) - 1
    child = (parent_a & mask) | (parent_b & ~mask)
    return child & ((1 << BITS) - 1)
