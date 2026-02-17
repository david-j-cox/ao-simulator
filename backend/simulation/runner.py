"""Simulation runner orchestrator."""

from dataclasses import dataclass, field
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
    condition_summaries: list[dict] = field(default_factory=list)


class SimulationRunner:
    """Orchestrates agent-environment interaction loop."""

    def __init__(self, agent: AbstractAgent, environment: AbstractEnvironment):
        self.agent = agent
        self.environment = environment

    def _run_condition(
        self,
        condition_num: int,
        label: str,
        global_step_offset: int,
    ) -> tuple[list[dict], dict]:
        """Run one condition phase without resetting the agent.

        Returns (steps, condition_summary).
        """
        state = self.environment.reset()
        available_actions = self.environment.get_available_actions()

        steps = []
        total_reinforcements = 0
        action_counts: dict[str, int] = {}
        done = False
        local_step = 0

        while not done:
            action = self.agent.select_action(state, available_actions)
            result = self.environment.step(action)

            local_step += 1
            global_step = global_step_offset + local_step

            if result.reinforced:
                total_reinforcements += 1
            action_counts[result.action_taken] = action_counts.get(result.action_taken, 0) + 1

            steps.append({
                "step": global_step,
                "state": str(result.state),
                "action": result.action_taken,
                "reinforced": result.reinforced,
                "schedule_id": result.schedule_id,
                "condition": condition_num,
            })

            self.agent.update(state, result.action_taken, result.reinforced, result.state)
            state = result.state
            done = result.done

        condition_summary = {
            "condition": condition_num,
            "label": label,
            "start_step": global_step_offset + 1,
            "end_step": global_step_offset + local_step,
            "total_steps": local_step,
            "total_reinforcements": total_reinforcements,
            "reinforcement_rate": total_reinforcements / local_step if local_step > 0 else 0,
            "action_counts": action_counts,
        }

        return steps, condition_summary

    def run(self, seed: int | None = None) -> SimulationResult:
        """Run a single-condition simulation to completion."""
        if seed is not None:
            np.random.seed(seed)

        self.agent.reset()
        steps, cond_summary = self._run_condition(
            condition_num=1,
            label="Default",
            global_step_offset=0,
        )

        summary = {
            "total_steps": cond_summary["total_steps"],
            "total_reinforcements": cond_summary["total_reinforcements"],
            "reinforcement_rate": cond_summary["reinforcement_rate"],
            "action_counts": cond_summary["action_counts"],
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

        return SimulationResult(
            config=config,
            steps=steps,
            summary=summary,
            condition_summaries=[cond_summary],
        )

    def run_multi_condition(
        self,
        conditions: list[dict],
        swap_env_fn,
        seed: int | None = None,
    ) -> SimulationResult:
        """Run a multi-condition experiment.

        Agent state persists across conditions. Only schedules change.

        Args:
            conditions: List of condition dicts with label, max_steps, and schedule info.
            swap_env_fn: Callable(env, condition_dict) that swaps schedules/max_steps on the environment.
            seed: Random seed.
        """
        if seed is not None:
            np.random.seed(seed)

        self.agent.reset()

        all_steps = []
        all_summaries = []
        global_offset = 0

        for i, cond in enumerate(conditions):
            swap_env_fn(self.environment, cond)

            steps, cond_summary = self._run_condition(
                condition_num=i + 1,
                label=cond["label"],
                global_step_offset=global_offset,
            )

            all_steps.extend(steps)
            all_summaries.append(cond_summary)
            global_offset += cond_summary["total_steps"]

        total_steps = sum(s["total_steps"] for s in all_summaries)
        total_reinforcements = sum(s["total_reinforcements"] for s in all_summaries)
        combined_action_counts: dict[str, int] = {}
        for s in all_summaries:
            for action, count in s["action_counts"].items():
                combined_action_counts[action] = combined_action_counts.get(action, 0) + count

        summary = {
            "total_steps": total_steps,
            "total_reinforcements": total_reinforcements,
            "reinforcement_rate": total_reinforcements / total_steps if total_steps > 0 else 0,
            "action_counts": combined_action_counts,
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
            "conditions": [c["label"] for c in conditions],
        }

        return SimulationResult(
            config=config,
            steps=all_steps,
            summary=summary,
            condition_summaries=all_summaries,
        )
