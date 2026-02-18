"""Tests for TwoChoiceEnvironment."""

import pytest
from schedules.reinforcement import FR, FI
from environments.two_choice import TwoChoiceEnvironment


class TestTwoChoiceEnvironment:
    def _make_env(self, sa=None, sb=None, max_steps=10):
        return TwoChoiceEnvironment(
            schedule_a=sa or FR(1),
            schedule_b=sb or FR(1),
            max_steps=max_steps,
        )

    def test_reset_returns_start(self):
        env = self._make_env()
        assert env.reset() == "start"

    def test_available_actions(self):
        env = self._make_env()
        assert env.get_available_actions() == ["choice_a", "choice_b"]

    def test_step_increments(self):
        env = self._make_env()
        env.reset()
        env.step("choice_a")
        assert env.step_count == 1

    def test_done_at_max_steps(self):
        env = self._make_env(max_steps=2)
        env.reset()
        r1 = env.step("choice_a")
        assert not r1.done
        r2 = env.step("choice_b")
        assert r2.done

    def test_choice_a_checks_schedule_a(self):
        env = self._make_env(sa=FR(1), sb=FR(100))
        env.reset()
        result = env.step("choice_a")
        assert result.reinforced
        assert result.schedule_id == "schedule_a"

    def test_choice_b_checks_schedule_b(self):
        env = self._make_env(sa=FR(100), sb=FR(1))
        env.reset()
        result = env.step("choice_b")
        assert result.reinforced
        assert result.schedule_id == "schedule_b"

    def test_non_chosen_gets_false_check(self):
        # FR(2) for schedule_b: choosing choice_a should call schedule_b.check(False)
        env = self._make_env(sa=FR(100), sb=FR(2))
        env.reset()
        env.step("choice_a")  # b gets check(False) → count stays 0
        env.step("choice_b")  # b gets check(True) → count=1
        r = env.step("choice_b")  # b gets check(True) → count=2 → reinforce
        assert r.reinforced

    def test_interval_ticks_both(self):
        sa = FI(2)
        sb = FI(3)
        env = self._make_env(sa=sa, sb=sb)
        env.reset()
        env.step("choice_a")  # tick both → sa elapsed=1
        r = env.step("choice_a")  # tick both → sa elapsed=2, armed; check(True) → reinforce
        assert r.reinforced

    def test_state_always_start(self):
        env = self._make_env()
        env.reset()
        result = env.step("choice_a")
        assert result.state == "start"

    def test_info_has_step(self):
        env = self._make_env()
        env.reset()
        result = env.step("choice_a")
        assert result.info["step"] == 1

    def test_reset_clears(self):
        env = self._make_env()
        env.reset()
        env.step("choice_a")
        env.step("choice_a")
        env.reset()
        assert env.step_count == 0

    def test_name(self):
        env = self._make_env()
        assert env.name == "two_choice"
