"""Tests for reinforcement schedule classes (FR, VR, FI, VI) and factory."""

import numpy as np
import pytest
from schedules.reinforcement import FR, VR, FI, VI, create_schedule


# ── FR ──────────────────────────────────────────────────────────────

class TestFR:
    def test_reinforce_every_nth(self):
        s = FR(3)
        results = [s.check(True) for _ in range(9)]
        assert results == [False, False, True, False, False, True, False, False, True]

    def test_non_targets_dont_count(self):
        s = FR(2)
        s.check(False)
        s.check(False)
        assert not s.check(False)
        assert not s.check(True)  # 1st target
        assert s.check(True)     # 2nd target → reinforce

    def test_reset_clears_count(self):
        s = FR(3)
        s.check(True)
        s.check(True)
        s.reset()
        assert s.count == 0

    def test_tick_is_noop(self):
        s = FR(5)
        s.tick()
        s.tick()
        assert s.count == 0

    def test_multiple_cycles(self):
        s = FR(2)
        for _ in range(4):
            s.check(True)
        # 2nd and 4th should reinforce
        s2 = FR(2)
        reinforcements = [s2.check(True) for _ in range(6)]
        assert reinforcements.count(True) == 3

    def test_value_1_edge(self):
        s = FR(1)
        assert s.check(True)
        assert s.check(True)
        assert s.check(True)


# ── VR ──────────────────────────────────────────────────────────────

class TestVR:
    def test_seeded_deterministic(self):
        np.random.seed(42)
        s1 = VR(5)
        results1 = [s1.check(True) for _ in range(50)]

        np.random.seed(42)
        s2 = VR(5)
        results2 = [s2.check(True) for _ in range(50)]
        assert results1 == results2

    def test_minimum_ratio_is_1(self):
        np.random.seed(42)
        s = VR(1)
        # next_ratio should always be >= 1
        assert s.next_ratio >= 1

    def test_non_targets_dont_count(self):
        s = VR(10)
        for _ in range(100):
            s.check(False)
        # Count should still be 0
        assert s.count == 0

    def test_reset_resamples(self):
        s = VR(5)
        old_ratio = s.next_ratio
        s.check(True)  # increment count
        s.reset()
        assert s.count == 0

    def test_tick_is_noop(self):
        s = VR(5)
        s.tick()
        assert s.count == 0


# ── FI ──────────────────────────────────────────────────────────────

class TestFI:
    def test_arms_after_n_ticks(self):
        s = FI(3)
        for _ in range(3):
            s.tick()
        assert s.armed

    def test_not_armed_before_interval(self):
        s = FI(3)
        for _ in range(2):
            s.tick()
        assert not s.armed
        assert not s.check(True)

    def test_non_target_when_armed_stays_armed(self):
        s = FI(2)
        s.tick()
        s.tick()
        assert s.armed
        s.check(False)
        assert s.armed  # non-target doesn't disarm

    def test_resets_after_reinforcement(self):
        s = FI(2)
        s.tick()
        s.tick()
        assert s.check(True)
        assert s.elapsed == 0
        assert not s.armed

    def test_value_1_edge(self):
        s = FI(1)
        s.tick()
        assert s.armed
        assert s.check(True)

    def test_multiple_cycles(self):
        s = FI(2)
        reinforced_count = 0
        for step in range(10):
            s.tick()
            if s.check(True):
                reinforced_count += 1
        assert reinforced_count >= 2


# ── VI ──────────────────────────────────────────────────────────────

class TestVI:
    def test_seeded_deterministic(self):
        np.random.seed(42)
        s1 = VI(5)
        results1 = []
        for _ in range(50):
            s1.tick()
            results1.append(s1.check(True))

        np.random.seed(42)
        s2 = VI(5)
        results2 = []
        for _ in range(50):
            s2.tick()
            results2.append(s2.check(True))
        assert results1 == results2

    def test_minimum_interval_is_1(self):
        np.random.seed(42)
        s = VI(1)
        assert s.next_interval >= 1

    def test_arms_and_resamples_after_reinforcement(self):
        s = VI(1)
        # Tick enough to arm
        for _ in range(100):
            s.tick()
            if s.check(True):
                break
        # After reinforcement, should have resampled interval
        assert s.elapsed == 0
        assert not s.armed

    def test_non_target_when_armed_stays_armed(self):
        s = VI(1)
        for _ in range(100):
            s.tick()
        assert s.armed
        s.check(False)
        assert s.armed

    def test_reset_clears_state(self):
        s = VI(5)
        for _ in range(10):
            s.tick()
        s.reset()
        assert s.elapsed == 0
        assert not s.armed


# ── Factory ─────────────────────────────────────────────────────────

class TestCreateSchedule:
    @pytest.mark.parametrize("name,cls", [("FR", FR), ("VR", VR), ("FI", FI), ("VI", VI)])
    def test_all_four_types(self, name, cls):
        s = create_schedule(name, 10)
        assert isinstance(s, cls)

    def test_case_insensitive(self):
        s = create_schedule("fr", 5)
        assert isinstance(s, FR)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown schedule type"):
            create_schedule("EXT", 10)
