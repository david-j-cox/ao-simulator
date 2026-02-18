"""Two-choice operant chamber environment."""

from typing import Any
from environments.base import AbstractEnvironment, StepResult
from schedules.reinforcement import Schedule


class TwoChoiceEnvironment(AbstractEnvironment):
    """Two-choice concurrent operant chamber.

    Two response options (choice_a, choice_b), each with its own reinforcement schedule.
    """

    def __init__(self, schedule_a: Schedule, schedule_b: Schedule, max_steps: int = 1000):
        self.schedule_a = schedule_a
        self.schedule_b = schedule_b
        self.max_steps = max_steps
        self.step_count = 0

    def reset(self) -> Any:
        self.schedule_a.reset()
        self.schedule_b.reset()
        self.step_count = 0
        return "start"

    def step(self, action: str) -> StepResult:
        self.step_count += 1

        # Tick interval schedules
        self.schedule_a.tick()
        self.schedule_b.tick()

        # Check reinforcement
        reinforced = False
        schedule_id = ""

        if action == "choice_a":
            reinforced = self.schedule_a.check(True)
            self.schedule_b.check(False)
            schedule_id = "schedule_a"
        elif action == "choice_b":
            reinforced = self.schedule_b.check(True)
            self.schedule_a.check(False)
            schedule_id = "schedule_b"

        done = self.step_count >= self.max_steps

        return StepResult(
            state="start",
            action_taken=action,
            reinforced=reinforced,
            schedule_id=schedule_id,
            done=done,
            reinforcement_magnitude=1.0 if reinforced else 0.0,
            info={"step": self.step_count},
        )

    def get_available_actions(self) -> list[str]:
        return ["choice_a", "choice_b"]

    @property
    def name(self) -> str:
        return "two_choice"
