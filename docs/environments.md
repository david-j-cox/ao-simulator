# Environments

This document describes the experimental environments available in AO Simulator, including their state spaces, action spaces, and reinforcement mechanics. For reinforcement schedule details, see the first section below.

## Reinforcement Schedules

All environments use one or more reinforcement schedules from `backend/schedules/reinforcement.py`. A schedule determines **when** a target response produces reinforcement.

### Schedule Types

**FR (Fixed Ratio)** — Reinforcement is delivered after every N-th target response. The count resets after each reinforcement.
- Parameter: `value` = number of required responses (e.g., FR 5 = every 5th response)
- `tick()` does nothing (ratio schedules are response-counted, not time-based)
- `check(is_target_response)` increments count on target responses, returns `True` when count reaches `value`

**VR (Variable Ratio)** — Reinforcement is delivered after a variable number of target responses drawn from an exponential distribution with mean = `value`. The requirement is resampled after each reinforcement.
- Parameter: `value` = mean number of required responses (e.g., VR 10 = ~10 responses on average)
- Each ratio requirement is `max(1, round(exponential(value)))`, so the minimum is always 1
- `tick()` does nothing

**FI (Fixed Interval)** — Reinforcement is available for the first target response after `value` time steps have elapsed. The timer resets after each reinforcement.
- Parameter: `value` = interval duration in steps (e.g., FI 30 = 30 steps)
- `tick()` increments elapsed time; once elapsed >= `value`, the schedule becomes "armed"
- `check(is_target_response)` returns `True` only when armed **and** the response is a target response

**VI (Variable Interval)** — Like FI, but the interval is drawn from an exponential distribution with mean = `value`. The interval is resampled after each reinforcement.
- Parameter: `value` = mean interval in steps (e.g., VI 30 = ~30 steps on average)
- Each interval is `max(1, round(exponential(value)))`

### How Schedules Interact with Environments

Every time step, the environment:
1. Calls `tick()` on all schedules (advances interval timers)
2. Calls `check(True)` on the schedule associated with the chosen action
3. Calls `check(False)` on other schedules (they track non-target responses but do not reinforce)

This means interval schedules accumulate time regardless of which action the agent selects, matching how concurrent VI-VI schedules operate in real experiments.

## Two-Choice Chamber

**Experimental analogue**: A standard two-key concurrent operant chamber, as used in matching law research.

**Source**: `backend/environments/two_choice.py`

### Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `schedule_a` | `Schedule` | — | Reinforcement schedule for choice A |
| `schedule_b` | `Schedule` | — | Reinforcement schedule for choice B |
| `max_steps` | `int` | 1000 | Maximum time steps per condition |

### State Space

The state is always the string `"start"`. There is no spatial or temporal state — the agent simply chooses between two options each step. (Q-Learning uses a sliding history window of past choices as its internal state representation.)

### Action Space

| Action | Description |
|---|---|
| `choice_a` | Respond on alternative A |
| `choice_b` | Respond on alternative B |

### Reinforcement Mechanics

Each time step:
1. Both schedules are ticked (`schedule_a.tick()`, `schedule_b.tick()`)
2. If the agent chose `choice_a`:
   - `schedule_a.check(True)` — may deliver reinforcement
   - `schedule_b.check(False)` — tracks the non-target response
3. If the agent chose `choice_b`:
   - `schedule_b.check(True)` — may deliver reinforcement
   - `schedule_a.check(False)` — tracks the non-target response

The `schedule_id` in `StepResult` reports which schedule delivered reinforcement (`"schedule_a"` or `"schedule_b"`).

### Multi-Condition Behavior

In multi-condition experiments, the Two-Choice Chamber:
- Resets its `step_count` and both schedules at the start of each condition
- Receives new schedules and `max_steps` via `_swap_env_schedules()`
- The agent is **not** reset — learned preferences carry over across conditions

This allows modeling phenomena like:
- **Extinction**: Switch from VI/VI to EXT/EXT (FR with value large enough to never trigger)
- **Resurgence**: Train A, train B, then extinguish both
- **Behavioral momentum**: Rich vs. lean baselines followed by disruption

## Grid Chamber

**Experimental analogue**: A spatial foraging arena or open-field test with a single operandum.

**Source**: `backend/environments/grid_chamber.py`

### Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `rows` | `int` | 5 | Number of grid rows |
| `cols` | `int` | 5 | Number of grid columns |
| `lever_pos` | `(int, int)` | (2, 2) | Row, column of the lever |
| `start_pos` | `(int, int)` | (0, 0) | Agent starting position |
| `schedule` | `Schedule` | — | Reinforcement schedule for lever presses |
| `max_steps` | `int` | 1000 | Maximum time steps per condition |

### State Space

The state is a tuple `(row, col)` representing the agent's position on the grid. Rows and columns are 0-indexed. The top-left corner is `(0, 0)`.

### Action Space

| Action | Effect |
|---|---|
| `up` | Move one row up (row - 1), clamped at 0 |
| `down` | Move one row down (row + 1), clamped at `rows - 1` |
| `left` | Move one column left (col - 1), clamped at 0 |
| `right` | Move one column right (col + 1), clamped at `cols - 1` |
| `stay` | Remain in current position |
| `press_lever` | Attempt to press the lever |

If `press_lever` is selected but the agent is **not** adjacent to the lever, the action is converted to `stay` (no movement, no lever press). Adjacency is defined as being within 1 step in both row and column (including diagonals).

### Reinforcement Mechanics

Each time step:
1. The lever schedule is ticked (`schedule.tick()`)
2. If the agent chose `press_lever` **and** is adjacent to the lever:
   - `schedule.check(True)` — may deliver reinforcement
   - `schedule_id` = `"lever_schedule"`
3. For all other actions (movement or failed lever press):
   - `schedule.check(False)` — tracks the non-target response

### Visit Tracking

The environment maintains a `visit_counts` dictionary mapping `(row, col)` tuples to visit counts. This is used by the frontend's `GridVisualization` component to render a heatmap of the agent's spatial behavior.

### Multi-Condition Behavior

In multi-condition experiments, the Grid Chamber:
- Resets position to `start_pos`, clears `visit_counts`, and resets the schedule at each condition start
- Receives a new schedule and `max_steps` via `_swap_env_schedules()`
- Grid dimensions and lever/start positions remain fixed across conditions
- The agent is **not** reset

## Comparison Table

| Feature | Two-Choice Chamber | Grid Chamber |
|---|---|---|
| State space | `"start"` (stateless) | `(row, col)` position |
| Action count | 2 | 6 |
| Schedules | 2 concurrent | 1 lever schedule |
| Reinforcement | On chosen alternative | On lever press when adjacent |
| Spatial | No | Yes (NxM grid) |
| Visit tracking | No | Yes (heatmap data) |
| Typical use | Matching law, choice | Foraging, approach behavior |
