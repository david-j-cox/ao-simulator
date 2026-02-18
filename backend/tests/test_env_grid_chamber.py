"""Tests for GridChamberEnvironment."""

import pytest
from schedules.reinforcement import FR, FI
from environments.grid_chamber import GridChamberEnvironment


def _make_levers(lever_specs):
    """Helper: create levers list from [(pos, schedule, magnitude), ...] tuples."""
    return [
        {"pos": pos, "schedule": sched, "magnitude": mag}
        for pos, sched, mag in lever_specs
    ]


class TestGridChamberEnvironment:
    def _make_env(self, levers=None, rows=5, cols=5,
                  start_pos=(0, 0), max_steps=100,
                  # Legacy single-lever shorthand
                  lever_pos=None, schedule=None):
        if levers is not None:
            return GridChamberEnvironment(
                rows=rows, cols=cols, levers=levers,
                max_steps=max_steps, start_pos=start_pos,
            )
        if lever_pos is not None or schedule is not None:
            return GridChamberEnvironment(
                rows=rows, cols=cols, lever_pos=lever_pos,
                schedule=schedule, max_steps=max_steps, start_pos=start_pos,
            )
        return GridChamberEnvironment(
            rows=rows, cols=cols, max_steps=max_steps, start_pos=start_pos,
        )

    def test_reset_returns_start_pos(self):
        env = self._make_env()
        assert env.reset() == (0, 0)

    def test_available_actions(self):
        env = self._make_env()
        assert set(env.get_available_actions()) == {
            "up", "down", "left", "right", "stay", "press_lever"
        }

    def test_move_down(self):
        env = self._make_env()
        env.reset()
        r = env.step("down")
        assert env.pos == (1, 0)

    def test_move_right(self):
        env = self._make_env()
        env.reset()
        r = env.step("right")
        assert env.pos == (0, 1)

    def test_move_up_boundary(self):
        env = self._make_env(start_pos=(0, 0))
        env.reset()
        env.step("up")
        assert env.pos == (0, 0)  # clamped

    def test_move_left_boundary(self):
        env = self._make_env(start_pos=(0, 0))
        env.reset()
        env.step("left")
        assert env.pos == (0, 0)

    def test_move_down_boundary(self):
        env = self._make_env(rows=3, start_pos=(2, 0))
        env.reset()
        env.step("down")
        assert env.pos == (2, 0)

    def test_move_right_boundary(self):
        env = self._make_env(cols=3, start_pos=(0, 2))
        env.reset()
        env.step("right")
        assert env.pos == (0, 2)

    def test_stay(self):
        env = self._make_env()
        env.reset()
        env.step("stay")
        assert env.pos == (0, 0)

    def test_press_lever_adjacent(self):
        # Start at (1, 2), lever at (2, 2) → adjacent
        levers = _make_levers([((2, 2), FR(1), 1.0)])
        env = self._make_env(levers=levers, start_pos=(1, 2))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced
        assert r.schedule_id == "lever_1_schedule"

    def test_press_lever_on_lever(self):
        # Start at lever position
        levers = _make_levers([((2, 2), FR(1), 1.0)])
        env = self._make_env(levers=levers, start_pos=(2, 2))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced

    def test_press_lever_not_adjacent(self):
        # Start at (0, 0), lever at (2, 2) → not adjacent
        levers = _make_levers([((2, 2), FR(1), 1.0)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        r = env.step("press_lever")
        assert not r.reinforced
        assert r.action_taken == "stay"  # converted to stay

    def test_non_lever_check_false(self):
        # Moving should call schedule.check(False)
        sched = FR(2)
        levers = _make_levers([((2, 2), sched, 1.0)])
        env = self._make_env(levers=levers)
        env.reset()
        env.step("down")  # check(False) on schedule
        assert sched.count == 0  # non-target doesn't increment FR count

    def test_visit_counts_tracked(self):
        env = self._make_env()
        env.reset()  # visits (0,0)
        env.step("down")  # visits (1,0)
        env.step("down")  # visits (2,0)
        env.step("up")   # visits (1,0) again
        assert env.visit_counts[(0, 0)] == 1
        assert env.visit_counts[(1, 0)] == 2
        assert env.visit_counts[(2, 0)] == 1

    def test_visit_counts_in_info(self):
        env = self._make_env()
        env.reset()
        r = env.step("down")
        assert "visit_counts" in r.info

    def test_done_at_max_steps(self):
        env = self._make_env(max_steps=2)
        env.reset()
        r1 = env.step("stay")
        assert not r1.done
        r2 = env.step("stay")
        assert r2.done

    def test_schedule_ticks(self):
        sched = FI(2)
        levers = _make_levers([((1, 0), sched, 1.0)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        env.step("down")  # tick 1, now at (1,0) on lever
        env.step("stay")  # tick 2 → armed
        r = env.step("press_lever")  # tick 3, check(True) → reinforce
        assert r.reinforced

    def test_no_schedule(self):
        env = self._make_env()
        env.reset()
        # Moving should not crash even without schedule
        r = env.step("down")
        assert not r.reinforced

    def test_reset_clears(self):
        env = self._make_env()
        env.reset()
        env.step("down")
        env.step("right")
        env.reset()
        assert env.pos == (0, 0)
        assert env.step_count == 0
        assert len(env.visit_counts) == 1  # just start pos

    def test_custom_dimensions(self):
        env = self._make_env(rows=3, cols=4)
        env.reset()
        assert env.rows == 3
        assert env.cols == 4

    def test_name(self):
        env = self._make_env()
        assert env.name == "grid_chamber"

    # ── Legacy single-lever interface ──────────────────────────────
    def test_legacy_lever_pos_and_schedule(self):
        env = self._make_env(lever_pos=(3, 3), schedule=FR(1))
        env.reset()
        assert len(env.levers) == 1
        assert env.levers[0]["pos"] == (3, 3)

    # ── Multi-lever tests ──────────────────────────────────────────

    def test_two_levers_adjacency(self):
        """Agent at (0,0) is adjacent to lever at (0,1) but not (4,4)."""
        levers = _make_levers([((0, 1), FR(1), 1.0), ((4, 4), FR(1), 2.0)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced
        assert r.schedule_id == "lever_1_schedule"
        assert r.reinforcement_magnitude == 1.0

    def test_second_lever_adjacency(self):
        """Agent at (4,4) is adjacent to lever 2 at (4,3) but not lever 1 at (0,0)."""
        levers = _make_levers([((0, 0), FR(1), 1.0), ((4, 3), FR(1), 2.0)])
        env = self._make_env(levers=levers, start_pos=(4, 4))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced
        assert r.schedule_id == "lever_2_schedule"
        assert r.reinforcement_magnitude == 2.0

    def test_all_lever_schedules_tick(self):
        """All lever schedules should tick on every step."""
        sched1 = FI(2)
        sched2 = FI(3)
        levers = _make_levers([((0, 1), sched1, 1.0), ((4, 4), sched2, 1.0)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        env.step("stay")  # tick 1
        env.step("stay")  # tick 2
        # After 2 ticks, sched1 (FI 2) should be armed
        assert sched1.armed

    def test_magnitude_in_step_result(self):
        """reinforcement_magnitude should reflect the lever's magnitude."""
        levers = _make_levers([((0, 1), FR(1), 3.5)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced
        assert r.reinforcement_magnitude == 3.5

    def test_zero_magnitude_still_reinforces(self):
        """magnitude=0 means the schedule fires but magnitude is 0 (extinction signal)."""
        levers = _make_levers([((0, 1), FR(1), 0.0)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced
        assert r.reinforcement_magnitude == 0.0

    def test_non_pressed_lever_gets_check_false(self):
        """When pressing lever 1, lever 2's schedule should get check(False)."""
        sched1 = FR(1)
        sched2 = FR(1)
        levers = _make_levers([((0, 1), sched1, 1.0), ((0, 0), sched2, 1.0)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        # Agent at (0,0), adjacent to both levers. First adjacent is lever 1 at (0,1)
        r = env.step("press_lever")
        # Lever 1 was pressed (check True), lever 2 gets check(False)
        assert r.schedule_id == "lever_1_schedule"

    def test_three_levers(self):
        """Support for 3 levers."""
        levers = _make_levers([
            ((0, 1), FR(1), 1.0),
            ((2, 2), FR(1), 2.0),
            ((4, 4), FR(1), 3.0),
        ])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        assert len(env.levers) == 3

    def test_reset_resets_all_lever_schedules(self):
        """reset() should reset every lever's schedule."""
        sched1 = FR(2)
        sched2 = FR(2)
        levers = _make_levers([((0, 1), sched1, 1.0), ((4, 4), sched2, 1.0)])
        env = self._make_env(levers=levers, start_pos=(0, 0))
        env.reset()
        # Do some steps
        env.step("press_lever")
        env.step("press_lever")
        # Reset
        env.reset()
        assert sched1.count == 0
        assert sched2.count == 0
