"""Tests for GridChamberEnvironment."""

import pytest
from schedules.reinforcement import FR, FI
from environments.grid_chamber import GridChamberEnvironment


class TestGridChamberEnvironment:
    def _make_env(self, schedule=None, rows=5, cols=5, lever_pos=(2, 2),
                  start_pos=(0, 0), max_steps=100):
        return GridChamberEnvironment(
            rows=rows, cols=cols, lever_pos=lever_pos,
            schedule=schedule, max_steps=max_steps, start_pos=start_pos,
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
        env = self._make_env(schedule=FR(1), lever_pos=(2, 2), start_pos=(1, 2))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced
        assert r.schedule_id == "lever_schedule"

    def test_press_lever_on_lever(self):
        # Start at lever position
        env = self._make_env(schedule=FR(1), lever_pos=(2, 2), start_pos=(2, 2))
        env.reset()
        r = env.step("press_lever")
        assert r.reinforced

    def test_press_lever_not_adjacent(self):
        # Start at (0, 0), lever at (2, 2) → not adjacent
        env = self._make_env(schedule=FR(1), lever_pos=(2, 2), start_pos=(0, 0))
        env.reset()
        r = env.step("press_lever")
        assert not r.reinforced
        assert r.action_taken == "stay"  # converted to stay

    def test_non_lever_check_false(self):
        # Moving should call schedule.check(False)
        sched = FR(2)
        env = self._make_env(schedule=sched)
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
        env = self._make_env(schedule=sched, lever_pos=(1, 0), start_pos=(0, 0))
        env.reset()
        env.step("down")  # tick 1, now at (1,0) adjacent to (1,0)... wait, lever_pos is (1,0)
        # Actually we're ON the lever now, so adjacent check passes
        env.step("stay")  # tick 2 → armed
        r = env.step("press_lever")  # tick 3, but FI armed at tick 2, check(True) → reinforce
        assert r.reinforced

    def test_no_schedule(self):
        env = self._make_env(schedule=None)
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

    def test_custom_start_and_lever(self):
        env = self._make_env(start_pos=(1, 1), lever_pos=(3, 3))
        assert env.reset() == (1, 1)
        assert env.lever_pos == (3, 3)

    def test_name(self):
        env = self._make_env()
        assert env.name == "grid_chamber"
