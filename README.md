# AO Simulator

A web-based research tool for behavior scientists to configure and run simulations of artificial organisms (AOs) under different reinforcement schedules. Researchers select an environment, choose a behavioral algorithm, configure schedule parameters, run the simulation, and download raw data as CSV or JSON.

## What It Does

AO Simulator models how artificial organisms allocate behavior across response options when exposed to reinforcement contingencies. It supports three established behavioral models and two experimental environments, enabling researchers to compare algorithmic predictions against known behavioral phenomena like the matching law, rate-dependent responding, and spatial foraging patterns.

### Environments

- **Two-Choice Chamber** — A concurrent operant arrangement with two response options (A and B), each associated with its own reinforcement schedule. Models standard concurrent VI-VI and ratio schedule preparations.
- **Grid Chamber** — An NxM grid with a lever at a configurable position. The organism navigates (up/down/left/right/stay) and can press the lever when adjacent. Models spatial foraging and approach behavior.

### Algorithms

- **Q-Learning** — Tabular reinforcement learning with epsilon-greedy action selection. Uses a sliding history window as state representation for two-choice, and (row, col) position for grid environments.
- **ETBD (Evolutionary Theory of Behavior Dynamics)** — A selectionist model of operant behavior based on McDowell (2004). Maintains a population of behavioral phenotypes that undergo selection, recombination, and mutation each time step. Reinforcement biases the population toward the reinforced response class; absence of reinforcement produces behavioral drift.
- **MPR (Mathematical Principles of Reinforcement)** — Based on Killeen's (1994) mathematical principles of reinforcement. Computes per-action coupling values from reinforcement rates, using exponential functions for ratio schedules and hyperbolic functions for interval schedules. Two-choice selection follows the matching law; grid selection uses softmax over couplings.

### Reinforcement Schedules

- **FR (Fixed Ratio)** — Reinforcement after every N-th target response
- **VR (Variable Ratio)** — Reinforcement after a geometrically-distributed count of target responses
- **FI (Fixed Interval)** — Reinforcement for the first target response after N time steps
- **VI (Variable Interval)** — Reinforcement for the first target response after an exponentially-distributed interval

## Project Structure

```
ao-simulator/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt
│   ├── api/
│   │   ├── routes.py            # POST /api/simulate, /csv, /json
│   │   └── schemas.py           # Pydantic request/response models
│   ├── environments/
│   │   ├── base.py              # AbstractEnvironment, StepResult
│   │   ├── two_choice.py        # TwoChoiceEnvironment
│   │   └── grid_chamber.py      # GridChamberEnvironment
│   ├── agents/
│   │   ├── base.py              # AbstractAgent ABC
│   │   ├── q_learning.py        # QLearningAgent
│   │   ├── etbd.py              # ETBDAgent
│   │   └── mpr.py               # MPRAgent
│   ├── schedules/
│   │   └── reinforcement.py     # FR, VR, FI, VI schedule classes
│   ├── simulation/
│   │   └── runner.py            # SimulationRunner orchestrator
│   └── etbd_internals/
│       ├── organism.py          # Population + emit/reinforce/drift
│       ├── selection.py         # Fitness-proportionate selection
│       ├── recombination.py     # Single-point crossover
│       ├── mutation.py          # Bit-flip mutation
│       └── fitness.py           # Circular fitness landscape
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx              # Router: ConfigPage / ResultsPage
        ├── api/client.js        # Fetch wrapper + download helpers
        ├── pages/
        │   ├── ConfigPage.jsx   # Environment, algorithm, schedule config
        │   └── ResultsPage.jsx  # Summary stats + data download
        └── components/
            ├── EnvironmentSelector.jsx
            ├── AlgorithmSelector.jsx
            ├── ScheduleConfig.jsx
            ├── GridConfig.jsx
            ├── AlgorithmParams.jsx
            └── GridVisualization.jsx   # Visit-frequency heatmap
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI runs on `http://localhost:5174` and proxies API requests to the backend.

## API

All simulation endpoints accept a POST with a JSON configuration body.

| Endpoint | Returns |
|---|---|
| `POST /api/simulate` | Full results as JSON (config, summary, step array) |
| `POST /api/simulate/csv` | Step-by-step data as downloadable CSV |
| `POST /api/simulate/json` | Full results as downloadable JSON file |

### Example Request

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

## Data Export

**CSV columns:** `step`, `state`, `action`, `reinforced`, `schedule_id`

**JSON structure:** Full nested object with `config` (echo of parameters), `summary` (aggregate stats, action counts), and `steps` (per-step records).

## References

- McDowell, J. J. (2004). A computational model of selection by consequences. *Journal of the Experimental Analysis of Behavior, 81*(3), 297–317.
- Killeen, P. R. (1994). Mathematical principles of reinforcement. *Behavioral and Brain Sciences, 17*(1), 105–135.
- Watkins, C. J. C. H., & Dayan, P. (1992). Q-learning. *Machine Learning, 8*(3), 279–292.

## License

MIT
