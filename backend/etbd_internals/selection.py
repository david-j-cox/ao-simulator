"""Fitness-search selection for ETBD."""

import numpy as np
from etbd_internals.fitness import fitness_value


def select_parent(
    population: list[int],
    target: int,
    max_val: int = 1024,
    decay: float = 0.95,
) -> int:
    """Select a parent from the population using fitness-proportionate selection.

    Args:
        population: List of phenotype integers.
        target: The reinforced phenotype target.
        max_val: Maximum phenotype value (circular wrap).
        decay: Fitness decay parameter.

    Returns:
        Selected phenotype.
    """
    fitnesses = np.array([
        fitness_value(p, target, max_val, decay) for p in population
    ])
    total = fitnesses.sum()
    if total == 0:
        return population[np.random.randint(len(population))]
    probs = fitnesses / total
    idx = np.random.choice(len(population), p=probs)
    return population[idx]
