"""Grid operant chamber environment."""

from typing import Any
from environments.base import AbstractEnvironment, StepResult
from schedules.reinforcement import Schedule


class GridChamberEnvironment(AbstractEnvironment):
    """Grid-based operant chamber.

    NxM grid with a lever at a fixed position. Agent can move (up/down/left/right),
    stay, or press_lever. Lever press only works if adjacent to lever.
    """

    DIRECTIONS = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
        "stay": (0, 0),
    }

    def __init__(
        self,
        rows: int = 5,
        cols: int = 5,
        lever_pos: tuple[int, int] = (2, 2),
        schedule: Schedule = None,
        max_steps: int = 1000,
        start_pos: tuple[int, int] = (0, 0),
    ):
        self.rows = rows
        self.cols = cols
        self.lever_pos = lever_pos
        self.schedule = schedule
        self.max_steps = max_steps
        self.start_pos = start_pos
        self.pos = start_pos
        self.step_count = 0
        self.visit_counts: dict[tuple[int, int], int] = {}

    def reset(self) -> Any:
        self.pos = self.start_pos
        self.step_count = 0
        self.visit_counts = {}
        if self.schedule:
            self.schedule.reset()
        self._record_visit(self.pos)
        return self.pos

    def _record_visit(self, pos: tuple[int, int]):
        self.visit_counts[pos] = self.visit_counts.get(pos, 0) + 1

    def _is_adjacent_to_lever(self) -> bool:
        r, c = self.pos
        lr, lc = self.lever_pos
        return abs(r - lr) <= 1 and abs(c - lc) <= 1

    def step(self, action: str) -> StepResult:
        self.step_count += 1

        if self.schedule:
            self.schedule.tick()

        actual_action = action
        reinforced = False
        schedule_id = ""

        if action == "press_lever":
            if self._is_adjacent_to_lever():
                reinforced = self.schedule.check(True) if self.schedule else False
                schedule_id = "lever_schedule"
            else:
                actual_action = "stay"
        elif action in self.DIRECTIONS:
            dr, dc = self.DIRECTIONS[action]
            new_r = max(0, min(self.rows - 1, self.pos[0] + dr))
            new_c = max(0, min(self.cols - 1, self.pos[1] + dc))
            self.pos = (new_r, new_c)
            if self.schedule:
                self.schedule.check(False)

        self._record_visit(self.pos)
        done = self.step_count >= self.max_steps

        return StepResult(
            state=self.pos,
            action_taken=actual_action,
            reinforced=reinforced,
            schedule_id=schedule_id,
            done=done,
            info={
                "step": self.step_count,
                "position": self.pos,
                "visit_counts": dict(self.visit_counts),
            },
        )

    def get_available_actions(self) -> list[str]:
        return ["up", "down", "left", "right", "stay", "press_lever"]

    @property
    def name(self) -> str:
        return "grid_chamber"
