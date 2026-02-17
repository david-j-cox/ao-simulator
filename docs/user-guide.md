# User Guide

This guide walks you through using AO Simulator to run experiments with artificial organisms. It is written for behavior scientists with minimal programming experience.

## Getting Started

### Prerequisites

- **Python 3.11+** — [Download from python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [Download from nodejs.org](https://nodejs.org/)

### Installation

1. **Clone or download** the AO Simulator repository.

2. **Install backend dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**:
   ```bash
   cd frontend
   npm install
   ```

### Running the Simulator

You need two terminal windows — one for the backend and one for the frontend.

**Terminal 1 — Backend**:
```bash
cd backend
uvicorn main:app --reload
```
The API starts on `http://localhost:8000`.

**Terminal 2 — Frontend**:
```bash
cd frontend
npm run dev
```
The UI starts on `http://localhost:5174`.

Open `http://localhost:5174` in your browser to use the simulator.

## Interface Overview

### Configuration Page

When you open the simulator, you see the configuration page with these sections:

1. **Environment** — Choose between:
   - *Two-Choice Chamber*: Two response alternatives with independent schedules (for matching law, choice studies)
   - *Grid Chamber*: Spatial grid with a lever (for foraging, approach behavior)

2. **Algorithm** — Choose between:
   - *Q-Learning*: Reinforcement learning with epsilon-greedy exploration
   - *ETBD*: Evolutionary model of operant behavior
   - *MPR*: Mathematical principles of reinforcement

3. **Multi-condition experiment** — Check this box to define multiple experimental phases (e.g., baseline then extinction). Each condition has its own schedule settings and step count.

4. **Schedule Configuration** — Set the reinforcement schedule(s):
   - Two-choice: Schedule A and Schedule B, each with a type (FR, VR, FI, VI) and value
   - Grid: One lever schedule with type and value

5. **Grid Configuration** (grid chamber only) — Set grid dimensions, lever position, and start position.

6. **Algorithm Parameters** — Adjust parameters specific to the chosen algorithm (see [Algorithms](algorithms.md) for details).

7. **Simulation Settings** — Set the maximum number of steps and an optional random seed for reproducibility.

8. **Run Simulation** — Click to start. The button shows "Running..." while the simulation executes.

### Results Page

After a simulation completes, you see:

1. **Summary** — Agent name, environment, total steps, total reinforcements, reinforcement rate.
2. **Action Counts** — How many times each action was taken and the proportion of total responses.
3. **Cumulative Record** — A line chart showing cumulative responses over time (see below).
4. **Per-Condition Breakdown** (multi-condition only) — Table showing steps, reinforcements, rate, and action counts for each condition.
5. **Grid Heatmap** (grid chamber only) — Color-coded grid showing how frequently the agent visited each cell.
6. **Download Data** — Buttons to download results as CSV or JSON.

Click **Back to Config** to return and run another simulation.

## Understanding the Cumulative Record

The cumulative record chart is a standard tool in behavior analysis. The x-axis shows time (step number) and the y-axis shows cumulative responses.

**Two-choice environment**: Two lines are plotted — one for Choice A (blue) and one for Choice B (red). The slope of each line represents the response rate for that alternative. Steeper = faster responding.

**Grid environment**: One line is plotted showing cumulative lever presses. Flat sections indicate periods where the agent is navigating the grid without pressing the lever.

**Multi-condition**: Vertical dashed lines mark the boundaries between conditions, labeled with the condition name. This lets you see how behavior changes when the contingencies shift.

## Demo Experiments

### Demo 1: Matching Law

**Goal**: Show that ETBD produces response allocation that matches the reinforcement ratio (Herrnstein, 1961).

**Setup**:
- Environment: Two-Choice Chamber
- Algorithm: ETBD
- Schedule A: VI 30
- Schedule B: VI 60
- Max Steps: 5000
- Seed: 42

**What to expect**: With a 2:1 reinforcement ratio (VI 30 delivers about twice as many reinforcers as VI 60), the agent should allocate approximately 2:1 responses to Choice A vs. Choice B. Check the Action Counts table — the proportion for `choice_a` should be roughly 60–70%.

**What to look for in the cumulative record**: The Choice A line should be steeper than the Choice B line, reflecting the higher response rate on the richer schedule.

### Demo 2: Behavioral Momentum

**Goal**: Show that behavior maintained by richer reinforcement is more resistant to disruption.

**Setup**:
- Environment: Two-Choice Chamber
- Algorithm: ETBD
- Multi-condition: Checked
- Condition 1 ("Rich Baseline"): 3000 steps, Schedule A: VI 10, Schedule B: VI 60
- Condition 2 ("Extinction"): 3000 steps, Schedule A: VI 10000, Schedule B: VI 10000

**What to expect**: During baseline, the agent allocates most responses to Choice A (richer schedule). When extinction begins, responding on both alternatives decreases, but Choice A (previously richer) should persist longer than Choice B. The cumulative record will show both lines flattening during extinction, but the Choice A line should continue rising slightly longer.

### Demo 3: Resurgence

**Goal**: Show that a previously reinforced response reappears when a more recently reinforced alternative is extinguished.

**Setup**:
- Environment: Two-Choice Chamber
- Algorithm: ETBD
- Multi-condition: Checked
- Condition 1 ("Train A"): 2000 steps, Schedule A: VI 30, Schedule B: VI 1000
- Condition 2 ("Train B"): 2000 steps, Schedule A: VI 1000, Schedule B: VI 30
- Condition 3 ("Extinction"): 2000 steps, Schedule A: VI 1000, Schedule B: VI 1000

**What to expect**:
- **Condition 1**: Agent learns to prefer Choice A
- **Condition 2**: Agent switches to Choice B (now the reinforced alternative)
- **Condition 3**: When both alternatives enter extinction, Choice A should temporarily reappear — this is resurgence. The cumulative record will show the Choice A line gaining slope again during extinction, even though it is not being reinforced.

### Demo 4: Grid Exploration

**Goal**: Show that Q-Learning learns an efficient path to the lever in a spatial environment.

**Setup**:
- Environment: Grid Chamber
- Algorithm: Q-Learning
- Schedule: FR 1
- Max Steps: 5000
- Grid: 5x5, lever at (2,2), start at (0,0)
- Q-Learning params: alpha=0.1, gamma=0.9, epsilon=0.1
- Seed: 42

**What to expect**: The grid heatmap should show a concentration of visits along the path from (0,0) to (2,2) and at cells adjacent to the lever. Early in the simulation, visits are spread out (exploration). Later, the agent follows a more direct path (exploitation). The cumulative lever-press line should become steeper over time as the agent learns to reach the lever faster.

## Working with Data

### CSV Format

The CSV download contains one row per time step with these columns:

| Column | Description |
|---|---|
| `step` | Global step number (1-indexed) |
| `state` | Environment state |
| `action` | Action taken |
| `reinforced` | `True` or `False` |
| `schedule_id` | Which schedule delivered reinforcement |
| `condition` | Condition number (1-indexed) |

You can open the CSV in Excel, Google Sheets, R, or Python for further analysis.

### JSON Format

The JSON download contains the complete simulation data:

```json
{
  "config": { ... },
  "summary": {
    "total_steps": 5000,
    "total_reinforcements": 150,
    "reinforcement_rate": 0.03,
    "action_counts": {"choice_a": 3200, "choice_b": 1800},
    "agent": "etbd",
    "environment": "two_choice",
    "agent_params": { ... }
  },
  "steps": [ ... ],
  "condition_summaries": [ ... ]
}
```

### Analysis Tips

**In Python (pandas)**:
```python
import pandas as pd

df = pd.read_csv("simulation_results.csv")

# Response counts per condition
df.groupby(["condition", "action"]).size()

# Reinforcement rate over time (rolling window)
df["reinforced_int"] = df["reinforced"].astype(int)
df["rolling_rate"] = df["reinforced_int"].rolling(100).mean()
```

**In R**:
```r
df <- read.csv("simulation_results.csv")

# Response counts per condition
table(df$condition, df$action)

# Reinforcement rate over time
library(zoo)
df$rolling_rate <- rollmean(as.numeric(df$reinforced), k = 100, fill = NA)
```

## Troubleshooting

**"Simulation failed" error**: Check that all required schedule fields are filled in. Two-choice requires both Schedule A and Schedule B. Grid chamber requires a lever schedule.

**Port 8000 already in use**: Another process is using port 8000. Stop it with `lsof -i :8000` to find the process, then kill it, or run the backend on a different port: `uvicorn main:app --reload --port 8001` (note: you'll also need to update the Vite proxy in `frontend/vite.config.js`).

**Frontend shows blank page**: Make sure the backend is running. The frontend proxies API requests to `http://localhost:8000` — if the backend is down, the simulation will fail.

**Slow simulation**: Reduce `max_steps` or `population_size` (for ETBD). Simulations with 100,000 steps and large populations may take several seconds.

**Results look random**: Set a `seed` value for reproducible results. Without a seed, each run uses a different random sequence.

**Multi-condition not showing condition boundaries**: Make sure you defined at least 2 conditions. A single condition behaves the same as a standard (non-multi-condition) run.
