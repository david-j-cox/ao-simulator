"""Simulation runner orchestrator."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from agents.base import AbstractAgent
from environments.base import AbstractEnvironment


@dataclass
class SimulationResult:
    """Container for simulation results."""
    config: dict
    steps: list[dict]
    summary: dict


class SimulationRunner:
    """Orchestrates agent-environment interaction loop."""

    def __init__(self, agent: AbstractAgent, environment: AbstractEnvironment):
        self.agent = agent
        self.environment = environment

    def run(self, seed: int | None = None) -> SimulationResult:
        """Run the simulation to completion."""
        if seed is not None:
            np.random.seed(seed)

        self.agent.reset()
        state = self.environment.reset()
        available_actions = self.environment.get_available_actions()

        steps = []
        total_reinforcements = 0
        action_counts: dict[str, int] = {}

        done = False
        step_num = 0

        while not done:
            action = self.agent.select_action(state, available_actions)
            result = self.environment.step(action)

            step_num += 1
            if result.reinforced:
                total_reinforcements += 1
            action_counts[result.action_taken] = action_counts.get(result.action_taken, 0) + 1

            steps.append({
                "step": step_num,
                "state": str(result.state),
                "action": result.action_taken,
                "reinforced": result.reinforced,
                "schedule_id": result.schedule_id,
            })

            self.agent.update(state, result.action_taken, result.reinforced, result.state)
            state = result.state
            done = result.done

        summary = {
            "total_steps": step_num,
            "total_reinforcements": total_reinforcements,
            "reinforcement_rate": total_reinforcements / step_num if step_num > 0 else 0,
            "action_counts": action_counts,
            "agent": self.agent.name,
            "environment": self.environment.name,
            "agent_params": self.agent.get_params(),
        }

        if hasattr(self.environment, 'visit_counts'):
            summary["visit_counts"] = {str(k): v for k, v in self.environment.visit_counts.items()}

        config = {
            "agent": self.agent.name,
            "environment": self.environment.name,
            "agent_params": self.agent.get_params(),
        }

        return SimulationResult(config=config, steps=steps, summary=summary)
