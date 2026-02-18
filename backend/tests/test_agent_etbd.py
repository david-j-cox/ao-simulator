"""Tests for ETBD agent."""

import numpy as np
import pytest
from agents.etbd import ETBDAgent, phenotype_to_action, action_to_target, TWO_CHOICE_MAP, GRID_MAP


class TestPhenotypeToAction:
    def test_two_choice_boundaries(self):
        assert phenotype_to_action(0, TWO_CHOICE_MAP) == "choice_a"
        assert phenotype_to_action(511, TWO_CHOICE_MAP) == "choice_a"
        assert phenotype_to_action(512, TWO_CHOICE_MAP) == "choice_b"
        assert phenotype_to_action(1023, TWO_CHOICE_MAP) == "choice_b"

    def test_grid_all_ranges(self):
        assert phenotype_to_action(0, GRID_MAP) == "up"
        assert phenotype_to_action(170, GRID_MAP) == "up"
        assert phenotype_to_action(171, GRID_MAP) == "down"
        assert phenotype_to_action(342, GRID_MAP) == "left"
        assert phenotype_to_action(513, GRID_MAP) == "right"
        assert phenotype_to_action(684, GRID_MAP) == "stay"
        assert phenotype_to_action(855, GRID_MAP) == "press_lever"
        assert phenotype_to_action(1023, GRID_MAP) == "press_lever"


class TestActionToTarget:
    def test_midpoints(self):
        assert action_to_target("choice_a", TWO_CHOICE_MAP) == 256
        assert action_to_target("choice_b", TWO_CHOICE_MAP) == 768
        assert action_to_target("up", GRID_MAP) == 85
        assert action_to_target("press_lever", GRID_MAP) == 939


class TestETBDAgent:
    def test_select_action_returns_valid(self):
        agent = ETBDAgent(environment_type="two_choice")
        action = agent.select_action("start", ["choice_a", "choice_b"])
        assert action in ["choice_a", "choice_b"]

    def test_update_reinforced(self):
        agent = ETBDAgent(population_size=20)
        old_pop = list(agent.organism.population)
        agent.update("s", "choice_a", True, "s2")
        assert agent.organism.population != old_pop

    def test_update_not_reinforced(self):
        agent = ETBDAgent(population_size=20)
        old_pop = list(agent.organism.population)
        agent.update("s", "choice_a", False, "s2")
        assert agent.organism.population != old_pop  # drift still changes

    def test_reset(self):
        agent = ETBDAgent(population_size=50)
        agent.update("s", "choice_a", True, "s2")
        agent.reset()
        assert len(agent.organism.population) == 50

    def test_grid_environment_type(self):
        agent = ETBDAgent(environment_type="grid_chamber")
        assert agent.action_map == GRID_MAP
        action = agent.select_action((0, 0), ["up", "down", "left", "right", "stay", "press_lever"])
        assert action in GRID_MAP

    def test_name(self):
        assert ETBDAgent().name == "etbd"

    def test_get_params(self):
        agent = ETBDAgent(population_size=200, mutation_rate=0.2, fitness_decay=0.9)
        p = agent.get_params()
        assert p["population_size"] == 200
        assert p["mutation_rate"] == 0.2
        assert p["fitness_decay"] == 0.9
