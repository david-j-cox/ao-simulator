"""Grid operant chamber environment."""

from typing import Any
from environments.base import AbstractEnvironment, StepResult
from schedules.reinforcement import Schedule


class GridChamberEnvironment(AbstractEnvironment):
    """Grid-based operant chamber.

    NxM grid with up to 8 levers at fixed positions. Agent can move
    (up/down/left/right), stay, or press_lever. Lever press only works
    if adjacent to a lever (first adjacent lever found).
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
        levers: list[dict] = None,
        max_steps: int = 1000,
        start_pos: tuple[int, int] = (0, 0),
        # Legacy single-lever params (deprecated, used for backward compat)
        lever_pos: tuple[int, int] = None,
        schedule: Schedule = None,
    ):
        self.rows = rows
        self.cols = cols
        self.max_steps = max_steps
        self.start_pos = start_pos
        self.pos = start_pos
        self.step_count = 0
        self.visit_counts: dict[tuple[int, int], int] = {}

        # Support legacy single-lever interface
        if levers is not None:
            self.levers = levers
        elif lever_pos is not None or schedule is not None:
            self.levers = [{
                "pos": lever_pos or (2, 2),
                "schedule": schedule,
                "magnitude": 1.0,
            }]
        else:
            self.levers = [{"pos": (2, 2), "schedule": None, "magnitude": 1.0}]

    def reset(self) -> Any:
        self.pos = self.start_pos
        self.step_count = 0
        self.visit_counts = {}
        for lever in self.levers:
            if lever["schedule"]:
                lever["schedule"].reset()
        self._record_visit(self.pos)
        return self.pos

    def _record_visit(self, pos: tuple[int, int]):
        self.visit_counts[pos] = self.visit_counts.get(pos, 0) + 1

    def _find_adjacent_lever(self) -> int | None:
        """Return the index of the first lever adjacent to agent, or None."""
        r, c = self.pos
        for i, lever in enumerate(self.levers):
            lr, lc = lever["pos"]
            if abs(r - lr) <= 1 and abs(c - lc) <= 1:
                return i
        return None

    def step(self, action: str) -> StepResult:
        self.step_count += 1

        # Tick ALL lever schedules
        for lever in self.levers:
            if lever["schedule"]:
                lever["schedule"].tick()

        actual_action = action
        reinforced = False
        schedule_id = ""
        magnitude = 0.0

        if action == "press_lever":
            lever_idx = self._find_adjacent_lever()
            if lever_idx is not None:
                lever = self.levers[lever_idx]
                if lever["schedule"]:
                    reinforced = lever["schedule"].check(True)
                schedule_id = f"lever_{lever_idx + 1}_schedule"
                magnitude = lever["magnitude"] if reinforced else 0.0
                # check(False) on non-pressed levers
                for j, other in enumerate(self.levers):
                    if j != lever_idx and other["schedule"]:
                        other["schedule"].check(False)
            else:
                actual_action = "stay"
                # check(False) on all lever schedules
                for lever in self.levers:
                    if lever["schedule"]:
                        lever["schedule"].check(False)
        elif action in self.DIRECTIONS:
            dr, dc = self.DIRECTIONS[action]
            new_r = max(0, min(self.rows - 1, self.pos[0] + dr))
            new_c = max(0, min(self.cols - 1, self.pos[1] + dc))
            self.pos = (new_r, new_c)
            # check(False) on ALL lever schedules
            for lever in self.levers:
                if lever["schedule"]:
                    lever["schedule"].check(False)

        self._record_visit(self.pos)
        done = self.step_count >= self.max_steps

        return StepResult(
            state=self.pos,
            action_taken=actual_action,
            reinforced=reinforced,
            schedule_id=schedule_id,
            done=done,
            reinforcement_magnitude=magnitude,
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
