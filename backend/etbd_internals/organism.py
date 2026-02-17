"""ETBD Organism: maintains a population of behaviors and emits responses."""

import numpy as np
from etbd_internals.selection import select_parent
from etbd_internals.recombination import recombine
from etbd_internals.mutation import mutate


class Organism:
    """An ETBD organism with a population of behavioral phenotypes.

    Each phenotype is an integer in [0, 1023] (10-bit representation).
    """

    def __init__(
        self,
        population_size: int = 100,
        mutation_rate: float = 0.1,
        fitness_decay: float = 0.95,
        max_phenotype: int = 1024,
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.fitness_decay = fitness_decay
        self.max_phenotype = max_phenotype
        self.population: list[int] = []
        self.reset()

    def reset(self):
        """Initialize population with random phenotypes."""
        self.population = [
            np.random.randint(0, self.max_phenotype)
            for _ in range(self.population_size)
        ]

    def emit(self) -> int:
        """Emit a response by randomly selecting from the population."""
        return self.population[np.random.randint(len(self.population))]

    def reinforce(self, target: int):
        """Apply selection, recombination, and mutation using the given target phenotype.

        This represents one generation of the genetic algorithm, selecting for
        behaviors near the reinforced target.
        """
        new_population = []
        for _ in range(self.population_size):
            parent_a = select_parent(
                self.population, target, self.max_phenotype, self.fitness_decay
            )
            parent_b = select_parent(
                self.population, target, self.max_phenotype, self.fitness_decay
            )
            child = recombine(parent_a, parent_b)
            child = mutate(child, self.mutation_rate)
            new_population.append(child)
        self.population = new_population

    def drift(self):
        """Apply random recombination and mutation without selection pressure.

        Used when no reinforcement occurs — parents are selected uniformly.
        """
        new_population = []
        for _ in range(self.population_size):
            parent_a = self.population[np.random.randint(len(self.population))]
            parent_b = self.population[np.random.randint(len(self.population))]
            child = recombine(parent_a, parent_b)
            child = mutate(child, self.mutation_rate)
            new_population.append(child)
        self.population = new_population
