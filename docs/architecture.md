# Architecture

This document describes the system architecture of the AO Simulator, covering both backend and frontend components, their interfaces, and how data flows through the system.

## High-Level Overview

AO Simulator is a two-tier web application:

```
┌─────────────────────┐        ┌──────────────────────┐
│   Frontend (React)  │  HTTP  │   Backend (FastAPI)   │
│   SPA on :5174      │───────>│   API on :8000        │
│                     │<───────│                       │
│  Vite dev server    │  JSON  │  uvicorn ASGI server  │
│  proxies /api/*     │        │                       │
└─────────────────────┘        └──────────────────────┘
```

- **Frontend**: A React single-page application served by Vite's dev server on port 5174. All `/api/*` requests are proxied to the backend.
- **Backend**: A FastAPI application served by uvicorn on port 8000. Handles simulation configuration, execution, and data export.

The frontend collects user configuration, sends a JSON request to `POST /api/simulate`, and renders the returned results. No persistent state exists on the server — each simulation request is self-contained.

## Backend Architecture

### Module Organization

```
backend/
├── main.py                    # FastAPI app, CORS middleware, router mount
├── api/
│   ├── routes.py              # Endpoint handlers and factory functions
│   └── schemas.py             # Pydantic request/response models
├── agents/
│   ├── base.py                # AbstractAgent ABC
│   ├── q_learning.py          # QLearningAgent
│   ├── etbd.py                # ETBDAgent
│   └── mpr.py                 # MPRAgent
├── environments/
│   ├── base.py                # AbstractEnvironment ABC, StepResult dataclass
│   ├── two_choice.py          # TwoChoiceEnvironment
│   └── grid_chamber.py        # GridChamberEnvironment
├── schedules/
│   └── reinforcement.py       # FR, VR, FI, VI classes + create_schedule factory
├── simulation/
│   └── runner.py              # SimulationRunner orchestrator
└── etbd_internals/
    ├── organism.py            # Population management, emit/reinforce/drift
    ├── selection.py           # Fitness-proportionate parent selection
    ├── recombination.py       # Single-point bitwise crossover
    ├── mutation.py            # Bit-flip mutation
    └── fitness.py             # Circular fitness landscape
```

### Agent Interface

Defined in `backend/agents/base.py`. All agents implement `AbstractAgent`:

| Method | Signature | Purpose |
|---|---|---|
| `select_action` | `(state, available_actions) -> str` | Choose an action given the current state and legal actions |
| `update` | `(state, action, reinforced, next_state) -> None` | Learn from the outcome of the action |
| `reset` | `() -> None` | Reset to initial state (clears learned parameters) |
| `get_params` | `() -> dict` | Return current parameters for logging |
| `name` | `@property -> str` | Agent name for display (e.g., `"q_learning"`) |

Agents do **not** reset between conditions in a multi-condition experiment. This allows learned behavior to carry over across experimental phases.

### Environment Interface

Defined in `backend/environments/base.py`. All environments implement `AbstractEnvironment`:

| Method | Signature | Purpose |
|---|---|---|
| `reset` | `() -> Any` | Reset environment and return the initial state |
| `step` | `(action: str) -> StepResult` | Execute an action, advance the environment, return the result |
| `get_available_actions` | `() -> list[str]` | Return valid action names |
| `name` | `@property -> str` | Environment name for display |

The `StepResult` dataclass returned by `step()`:

| Field | Type | Description |
|---|---|---|
| `state` | `Any` | New environment state after the action |
| `action_taken` | `str` | The action that was actually executed (may differ from input) |
| `reinforced` | `bool` | Whether reinforcement was delivered |
| `schedule_id` | `str` | Which schedule delivered the reinforcement |
| `done` | `bool` | Whether the episode has ended (max steps reached) |
| `info` | `dict` | Additional data (step count, position, visit counts) |

### Schedule Interface

Defined in `backend/schedules/reinforcement.py`. All schedules extend the `Schedule` ABC:

| Method | Signature | Purpose |
|---|---|---|
| `reset` | `() -> None` | Reset internal counters |
| `check` | `(is_target_response: bool) -> bool` | Return `True` if reinforcement should be delivered |
| `tick` | `() -> None` | Advance one time step (meaningful for interval schedules) |

The `create_schedule(schedule_type, value)` factory creates a schedule by name (`"FR"`, `"VR"`, `"FI"`, `"VI"`).

### Simulation Loop

`SimulationRunner` in `backend/simulation/runner.py` orchestrates the agent-environment interaction:

**Single-condition** (`run(seed=None)`):
1. Set random seed if provided
2. Reset the agent
3. Run `_run_condition()` — loop of `select_action` -> `step` -> `update` until `done`
4. Return `SimulationResult` with config, steps, summary, and condition_summaries

**Multi-condition** (`run_multi_condition(conditions, swap_env_fn, seed=None)`):
1. Set random seed if provided
2. Reset the agent **once**
3. For each condition:
   - Call `swap_env_fn(env, condition_dict)` to reconfigure schedules and max_steps
   - Run `_run_condition()` with a global step offset
   - Agent state is **preserved** across conditions
4. Aggregate results and return

### Request Processing Flow

When a request arrives at `POST /api/simulate`:

```
Request JSON
    │
    ▼
SimulationRequest (Pydantic validation)
    │
    ├── Has conditions? ─── Yes ──> _build_environment_for_condition(first)
    │                                _build_agent(req)
    │                                runner.run_multi_condition(...)
    │
    └── No ─────────────────────> _build_environment(req)
                                   _build_agent(req)
                                   runner.run(seed)
    │
    ▼
SimulationResult
    │
    ▼
SimulationResponse (JSON) / CSV / JSON file
```

Factory functions in `backend/api/routes.py`:
- `_build_environment(req)` — Creates a `TwoChoiceEnvironment` or `GridChamberEnvironment` from request fields
- `_build_agent(req)` — Creates a `QLearningAgent`, `ETBDAgent`, or `MPRAgent` from request fields
- `_swap_env_schedules(env, cond_dict)` — Swaps schedules and max_steps on an existing environment for multi-condition runs

## Frontend Architecture

### Component Hierarchy

```
App.jsx
├── ConfigPage.jsx              ← when results === null
│   ├── EnvironmentSelector     ← two_choice / grid_chamber radio
│   ├── AlgorithmSelector       ← q_learning / etbd / mpr radio
│   ├── ConditionEditor         ← multi-condition toggle + per-condition config
│   │   (or ScheduleConfig)     ← single-condition schedule inputs
│   ├── GridConfig              ← grid dimensions / lever / start (grid only)
│   ├── AlgorithmParams         ← algorithm-specific parameter inputs
│   └── [Simulation Settings]   ← max_steps, seed, Run button
│
└── ResultsPage.jsx             ← when results !== null
    ├── Summary table           ← agent, environment, steps, reinforcements
    ├── Action counts table
    ├── CumulativeRecordChart   ← recharts LineChart
    ├── Per-condition breakdown ← multi-condition table (if applicable)
    ├── GridVisualization       ← visit heatmap (grid_chamber only)
    └── Download buttons        ← CSV / JSON
```

### State Management

`App.jsx` uses a single `useState(null)` for `results`:
- `null` → render `ConfigPage`
- non-null → render `ResultsPage`

`ConfigPage` manages all form state locally (environment, algorithm, schedules, params, conditions). On "Run Simulation", it calls `runSimulation(config)` and passes the response up via `onResults`.

### API Client

`frontend/src/api/client.js` provides three functions:

- `runSimulation(config)` — `POST /api/simulate`, returns parsed JSON
- `downloadCSV(config)` — `POST /api/simulate/csv`, triggers browser file download
- `downloadJSON(config)` — `POST /api/simulate/json`, triggers browser file download

All requests are sent to `/api/*`, which Vite's dev server proxies to `http://localhost:8000` (configured in `vite.config.js`).

## Data Flow Diagram

```
User configures experiment in browser
         │
         ▼
ConfigPage.buildRequest()  ──>  JSON body
         │
         ▼
fetch("POST /api/simulate")
         │
    Vite proxy (:5174 -> :8000)
         │
         ▼
FastAPI route handler
         │
    ┌────┴─────────────────────┐
    │  _build_environment()    │
    │  _build_agent()          │
    │  SimulationRunner.run()  │
    │    ┌─────────────────┐   │
    │    │ loop:            │   │
    │    │  select_action() │   │
    │    │  env.step()      │   │
    │    │  agent.update()  │   │
    │    └─────────────────┘   │
    └──────────────────────────┘
         │
         ▼
SimulationResponse JSON
         │
    Vite proxy (:8000 -> :5174)
         │
         ▼
ResultsPage renders:
  - Summary stats table
  - Cumulative record chart
  - Condition breakdown (multi-condition)
  - Grid heatmap (grid_chamber)
  - CSV/JSON download buttons
```
