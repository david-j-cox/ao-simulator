# API Reference

The AO Simulator backend exposes a REST API for running simulations and exporting data. All endpoints accept JSON request bodies and are served at `http://localhost:8000`.

## Endpoints

| Method | Path | Description | Response |
|---|---|---|---|
| `GET` | `/` | Health check / version info | `{"message": "AO Simulator API", "version": "0.1.0"}` |
| `POST` | `/api/simulate` | Run simulation, return full results | JSON (`SimulationResponse`) |
| `POST` | `/api/simulate/csv` | Run simulation, return step data as CSV | CSV file download |
| `POST` | `/api/simulate/json` | Run simulation, return full results as JSON file | JSON file download |

All three `POST` endpoints accept the same `SimulationRequest` body. The only difference is the response format.

## Request Schema: `SimulationRequest`

### Top-Level Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `environment` | string | Yes | — | `"two_choice"` or `"grid_chamber"` |
| `algorithm` | string | Yes | — | `"q_learning"`, `"etbd"`, or `"mpr"` |
| `max_steps` | integer | No | 1000 | Maximum simulation steps (1–100,000) |
| `seed` | integer | No | null | Random seed for reproducibility |
| `schedule_a` | ScheduleConfig | Conditional | null | Schedule for choice A (required for single-condition two_choice) |
| `schedule_b` | ScheduleConfig | Conditional | null | Schedule for choice B (required for single-condition two_choice) |
| `schedule` | ScheduleConfig | Conditional | null | Lever schedule (required for single-condition grid_chamber) |
| `q_learning_params` | QLearningParams | No | null | Q-Learning parameters (used when `algorithm` = `"q_learning"`) |
| `etbd_params` | ETBDParams | No | null | ETBD parameters (used when `algorithm` = `"etbd"`) |
| `mpr_params` | MPRParams | No | null | MPR parameters (used when `algorithm` = `"mpr"`) |
| `grid_config` | GridConfig | No | null | Grid dimensions and positions (used when `environment` = `"grid_chamber"`) |
| `conditions` | list[ConditionConfig] | No | null | Up to 6 conditions for multi-phase experiments |

When `conditions` is provided and non-empty, the `schedule_a`/`schedule_b`/`schedule` and `max_steps` top-level fields are ignored in favor of per-condition settings.

### ScheduleConfig

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `type` | string | Yes | `"FR"`, `"VR"`, `"FI"`, or `"VI"` | Schedule type |
| `value` | integer | Yes | > 0 | Schedule parameter value |

### QLearningParams

| Field | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `alpha` | float | 0.1 | [0, 1] | Learning rate |
| `gamma` | float | 0.9 | [0, 1] | Discount factor |
| `epsilon` | float | 0.1 | [0, 1] | Exploration rate |
| `history_window` | int | 3 | >= 1 | State history window size (two-choice only) |

### ETBDParams

| Field | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `population_size` | int | 100 | >= 10 | Population size |
| `mutation_rate` | float | 0.1 | [0, 1] | Bit-flip mutation rate |
| `fitness_decay` | float | 0.95 | [0, 1] | Fitness decay parameter |

### MPRParams

| Field | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `initial_arousal` | float | 1.0 | > 0 | Specific activation parameter (a) |
| `activation_decay` | float | 0.95 | > 0 | Arousal decay parameter (b) |
| `coupling_floor` | float | 0.01 | >= 0 | Minimum coupling value |
| `temperature` | float | 1.0 | > 0 | Softmax temperature (grid only) |

### GridConfig

| Field | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `rows` | int | 5 | [2, 20] | Grid rows |
| `cols` | int | 5 | [2, 20] | Grid columns |
| `lever_row` | int | 2 | >= 0 | Lever row position |
| `lever_col` | int | 2 | >= 0 | Lever column position |
| `start_row` | int | 0 | >= 0 | Agent start row |
| `start_col` | int | 0 | >= 0 | Agent start column |

### ConditionConfig

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `label` | string | Yes | — | Condition label (e.g., "Baseline", "Extinction") |
| `max_steps` | int | No | 1000 | Steps for this condition (1–100,000) |
| `schedule_a` | ScheduleConfig | Conditional | null | Schedule A (required for two_choice) |
| `schedule_b` | ScheduleConfig | Conditional | null | Schedule B (required for two_choice) |
| `schedule` | ScheduleConfig | Conditional | null | Lever schedule (required for grid_chamber) |

## Response Schema: `SimulationResponse`

### Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `config` | dict | Echo of the simulation configuration |
| `summary` | dict | Aggregate statistics |
| `steps` | list[StepData] | Per-step records |
| `condition_summaries` | list[ConditionSummary] | Per-condition breakdowns |

### StepData

| Field | Type | Description |
|---|---|---|
| `step` | int | Global step number (1-indexed) |
| `state` | string | Environment state (e.g., `"start"` or `"(2, 3)"`) |
| `action` | string | Action taken |
| `reinforced` | bool | Whether reinforcement was delivered |
| `schedule_id` | string | Which schedule delivered reinforcement (empty if none) |
| `condition` | int | Condition number (1-indexed) |

### ConditionSummary

| Field | Type | Description |
|---|---|---|
| `condition` | int | Condition number (1-indexed) |
| `label` | string | Condition label |
| `start_step` | int | First global step in this condition |
| `end_step` | int | Last global step in this condition |
| `total_steps` | int | Number of steps in this condition |
| `total_reinforcements` | int | Number of reinforcements delivered |
| `reinforcement_rate` | float | Reinforcements / total steps |
| `action_counts` | dict[str, int] | Count of each action taken |

## Example Requests

### Single-Condition Two-Choice

ETBD on concurrent VI 30 / VI 60 for 5000 steps:

```json
{
  "environment": "two_choice",
  "algorithm": "etbd",
  "max_steps": 5000,
  "seed": 42,
  "schedule_a": { "type": "VI", "value": 30 },
  "schedule_b": { "type": "VI", "value": 60 },
  "etbd_params": {
    "population_size": 100,
    "mutation_rate": 0.1,
    "fitness_decay": 0.95
  }
}
```

### Single-Condition Grid Chamber

Q-Learning on a 5x5 grid with FR 1 for 2000 steps:

```json
{
  "environment": "grid_chamber",
  "algorithm": "q_learning",
  "max_steps": 2000,
  "seed": 42,
  "schedule": { "type": "FR", "value": 1 },
  "grid_config": {
    "rows": 5,
    "cols": 5,
    "lever_row": 2,
    "lever_col": 2,
    "start_row": 0,
    "start_col": 0
  },
  "q_learning_params": {
    "alpha": 0.1,
    "gamma": 0.9,
    "epsilon": 0.1,
    "history_window": 3
  }
}
```

### Multi-Condition Resurgence

ETBD with three conditions — train choice A, train choice B, then extinction of both:

```json
{
  "environment": "two_choice",
  "algorithm": "etbd",
  "max_steps": 1000,
  "seed": 42,
  "etbd_params": {
    "population_size": 100,
    "mutation_rate": 0.1,
    "fitness_decay": 0.95
  },
  "conditions": [
    {
      "label": "Train A",
      "max_steps": 2000,
      "schedule_a": { "type": "VI", "value": 30 },
      "schedule_b": { "type": "VI", "value": 1000 }
    },
    {
      "label": "Train B",
      "max_steps": 2000,
      "schedule_a": { "type": "VI", "value": 1000 },
      "schedule_b": { "type": "VI", "value": 30 }
    },
    {
      "label": "Extinction",
      "max_steps": 2000,
      "schedule_a": { "type": "VI", "value": 1000 },
      "schedule_b": { "type": "VI", "value": 1000 }
    }
  ]
}
```

## Usage Examples

### curl

```bash
# Run simulation and get JSON response
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "two_choice",
    "algorithm": "etbd",
    "max_steps": 1000,
    "schedule_a": {"type": "VI", "value": 30},
    "schedule_b": {"type": "VI", "value": 60}
  }'

# Download CSV
curl -X POST http://localhost:8000/api/simulate/csv \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "two_choice",
    "algorithm": "etbd",
    "max_steps": 1000,
    "schedule_a": {"type": "VI", "value": 30},
    "schedule_b": {"type": "VI", "value": 60}
  }' -o results.csv

# Download JSON file
curl -X POST http://localhost:8000/api/simulate/json \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "two_choice",
    "algorithm": "etbd",
    "max_steps": 1000,
    "schedule_a": {"type": "VI", "value": 30},
    "schedule_b": {"type": "VI", "value": 60}
  }' -o results.json
```

### Python (requests)

```python
import requests

config = {
    "environment": "two_choice",
    "algorithm": "etbd",
    "max_steps": 5000,
    "seed": 42,
    "schedule_a": {"type": "VI", "value": 30},
    "schedule_b": {"type": "VI", "value": 60},
    "etbd_params": {
        "population_size": 100,
        "mutation_rate": 0.1,
        "fitness_decay": 0.95,
    },
}

# Get full results
response = requests.post("http://localhost:8000/api/simulate", json=config)
data = response.json()

print(f"Total steps: {data['summary']['total_steps']}")
print(f"Action counts: {data['summary']['action_counts']}")

# Download CSV
csv_response = requests.post("http://localhost:8000/api/simulate/csv", json=config)
with open("results.csv", "w") as f:
    f.write(csv_response.text)
```

## Error Handling

The API returns standard HTTP error codes with a JSON body:

| Status | Cause | Example |
|---|---|---|
| 400 | Invalid configuration | Missing required schedule, unknown environment or algorithm |
| 422 | Validation error | Field out of range, wrong type |

Error response format:

```json
{
  "detail": "two_choice requires schedule_a and schedule_b"
}
```

Validation errors (422) return the standard Pydantic error format:

```json
{
  "detail": [
    {
      "loc": ["body", "max_steps"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```
