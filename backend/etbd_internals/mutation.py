"""Bit-flip mutation for ETBD."""

import numpy as np

BITS = 10  # 2^10 = 1024 phenotype values


def mutate(phenotype: int, mutation_rate: float = 0.1) -> int:
    """Apply bit-flip mutation to a phenotype.

    Each bit is flipped with probability mutation_rate.
    """
    for bit in range(BITS):
        if np.random.random() < mutation_rate:
            phenotype ^= (1 << bit)
    return phenotype
