# Algorithms

This document describes the three behavioral algorithms implemented in AO Simulator: Q-Learning, ETBD, and MPR. Each section covers the theoretical basis, implementation details, parameters, and expected behavior.

## Q-Learning

### Theory

Q-Learning (Watkins & Dayan, 1992) is a model-free reinforcement learning algorithm that learns action-value estimates without requiring a model of the environment. The agent maintains a table of Q-values, Q(s, a), representing the expected cumulative reward for taking action *a* in state *s*.

The update rule is:

```
Q(s, a) ← Q(s, a) + α [r + γ max_a' Q(s', a') - Q(s, a)]
```

where:
- *α* is the learning rate
- *r* is the reward (1 if reinforced, 0 otherwise)
- *γ* is the discount factor
- *s'* is the next state

Action selection uses epsilon-greedy: with probability *ε* the agent selects a random action, otherwise it selects the action with the highest Q-value (ties broken randomly).

### State Representation

**Two-Choice Chamber**: Since the environment state is always `"start"`, the agent uses a **sliding history window** of the last *N* choices as its state. For example, with `history_window=3`, the state might be `("choice_a", "choice_b", "choice_a")`. This allows the agent to learn sequential patterns.

**Grid Chamber**: The state is the agent's `(row, col)` position. No history window is used — spatial position provides sufficient state differentiation.

### Parameters

| Parameter | Type | Default | Range | Description |
|---|---|---|---|---|
| `alpha` | float | 0.1 | [0, 1] | Learning rate — how much new information overrides old Q-values |
| `gamma` | float | 0.9 | [0, 1] | Discount factor — weight of future rewards vs. immediate reward |
| `epsilon` | float | 0.1 | [0, 1] | Exploration rate — probability of choosing a random action |
| `history_window` | int | 3 | [1, ∞) | Number of past choices used as state (two-choice only) |

### Expected Behavior

- On concurrent VI-VI schedules, Q-Learning tends to **maximize** rather than match — it will preferentially allocate responses to the richer schedule but may not approximate the matching law as closely as ETBD or MPR.
- On grid environments, Q-Learning efficiently learns the shortest path to the lever.
- Lower epsilon values produce less exploration and faster convergence but risk suboptimal behavior if initial Q-values are misleading.

### Limitations

- The history-window state representation for two-choice may not capture long-range dependencies.
- Tabular Q-Learning does not generalize across similar states — each state-action pair is learned independently.
- The agent cannot model temporal dynamics of interval schedules (it treats reinforcement as binary feedback).

**Source**: `backend/agents/q_learning.py`

---

## ETBD (Evolutionary Theory of Behavior Dynamics)

### Theory

ETBD (McDowell, 2004) models operant behavior as an evolutionary process. Instead of learning value estimates, the agent maintains a **population of behavioral phenotypes** — integers in the range [0, 1023] (10-bit binary representation). Each phenotype maps to an action via response class boundaries.

The behavioral cycle on each time step:
1. **Emit**: Randomly sample one phenotype from the population. Map it to an action.
2. **Reinforce or Drift**:
   - If reinforced: apply **selection, recombination, and mutation** to produce a new generation, biased toward the reinforced response class.
   - If not reinforced: apply **drift** — recombination and mutation with uniform (unbiased) parent selection.

### Response Class Mapping

Phenotypes (integers 0–1023) are partitioned into response classes:

**Two-Choice**:
| Action | Phenotype Range |
|---|---|
| `choice_a` | [0, 512) |
| `choice_b` | [512, 1024) |

**Grid Chamber**:
| Action | Phenotype Range |
|---|---|
| `up` | [0, 171) |
| `down` | [171, 342) |
| `left` | [342, 513) |
| `right` | [513, 684) |
| `stay` | [684, 855) |
| `press_lever` | [855, 1024) |

### Genetic Operators

**Selection** (`backend/etbd_internals/selection.py`): Fitness-proportionate selection. Each phenotype's fitness is computed using a **circular fitness landscape** — an exponential decay function based on the circular distance between the phenotype and the reinforced target:

```
fitness(p, target) = decay ^ circular_distance(p, target)
```

Circular distance wraps around the phenotype space: `min(|p - target|, 1024 - |p - target|)`. Parents are selected with probability proportional to their fitness.

**Recombination** (`backend/etbd_internals/recombination.py`): Single-point crossover. A random crossover point (1–9) is selected. Bits below the point come from parent A; bits at or above come from parent B.

**Mutation** (`backend/etbd_internals/mutation.py`): Independent bit-flip mutation. Each of the 10 bits is flipped with probability = `mutation_rate`.

### Parameters

| Parameter | Type | Default | Range | Description |
|---|---|---|---|---|
| `population_size` | int | 100 | [10, ∞) | Number of phenotypes in the population |
| `mutation_rate` | float | 0.1 | [0, 1] | Per-bit probability of flipping during mutation |
| `fitness_decay` | float | 0.95 | [0, 1] | Exponential decay rate in the fitness landscape |

### Expected Behavior

- On concurrent VI-VI schedules, ETBD produces **matching** — the response ratio approximates the reinforcement ratio, consistent with the matching law (Herrnstein, 1961).
- ETBD exhibits **behavioral variability** even at steady state because the population always contains phenotypic diversity.
- In multi-condition experiments, ETBD naturally produces **behavioral momentum** and **resurgence** because the population retains a "memory" of previously reinforced response classes.
- Higher mutation rates increase behavioral variability; lower rates produce tighter response allocation.
- Higher fitness decay values create a narrower selection gradient, producing more precise response allocation.

**Sources**: `backend/agents/etbd.py`, `backend/etbd_internals/organism.py`, `backend/etbd_internals/fitness.py`, `backend/etbd_internals/selection.py`, `backend/etbd_internals/recombination.py`, `backend/etbd_internals/mutation.py`

---

## MPR (Mathematical Principles of Reinforcement)

### Theory

MPR (Killeen, 1994) is a mathematical framework that derives response rates and choice proportions from reinforcement rates. The key construct is **coupling** (*C*) — the strength of association between a response and its reinforcer.

Coupling depends on the schedule type:

**Ratio schedules (FR, VR)** — Exponential coupling:
```
C = a * exp(-b / R)
```

**Interval schedules (FI, VI)** — Hyperbolic coupling:
```
C = a * R / (R + b)
```

where:
- *R* = reinforcement rate (reinforcements per response for that action)
- *a* = initial arousal (specific activation parameter)
- *b* = activation decay

### Action Selection

**Two-Choice**: The matching law — probability of choosing action A is proportional to its coupling:

```
P(A) = C_A / (C_A + C_B)
```

**Grid Chamber**: Softmax over coupling values:

```
P(a_i) = exp(C_i / τ) / Σ exp(C_j / τ)
```

where *τ* is the temperature parameter.

### Parameters

| Parameter | Type | Default | Range | Description |
|---|---|---|---|---|
| `initial_arousal` | float | 1.0 | (0, ∞) | Specific activation parameter (*a*) — scales overall coupling |
| `activation_decay` | float | 0.95 | (0, ∞) | Arousal/decay parameter (*b*) — controls sensitivity to reinforcement rate |
| `coupling_floor` | float | 0.01 | [0, ∞) | Minimum coupling value (prevents zero-probability actions) |
| `temperature` | float | 1.0 | (0, ∞) | Softmax temperature (grid chamber only) — lower = more deterministic |

### Expected Behavior

- On concurrent VI-VI schedules, MPR directly implements the matching law and produces accurate matching from early in the session (no learning curve).
- On ratio schedules, the exponential coupling function produces higher response rates for richer schedules.
- MPR does **not** have a learning curve in the traditional sense — coupling is computed from cumulative reinforcement statistics. Early behavior may be variable due to small sample sizes.
- The `coupling_floor` parameter ensures that all actions maintain some minimum probability, preventing the agent from permanently abandoning an alternative.

### Limitations

- MPR computes coupling from aggregate reinforcement rates, not trial-by-trial updating. It does not model sequential dependencies or local response patterns.
- In multi-condition experiments, the cumulative nature of reinforcement tracking means that statistics from early conditions influence coupling in later conditions. This can slow adaptation to schedule changes.
- The coupling formulas assume steady-state behavior and may not accurately model transient dynamics.

**Source**: `backend/agents/mpr.py`

---

## Comparison Table

| Feature | Q-Learning | ETBD | MPR |
|---|---|---|---|
| Theoretical basis | Reinforcement learning | Selectionist / evolutionary | Mathematical behavior theory |
| State representation | History window or position | None (population-based) | None (rate-based) |
| Learning mechanism | Q-value update rule | Selection + genetic operators | Cumulative reinforcement statistics |
| Matching law | Approximate (tends to maximize) | Emergent (population dynamics) | Direct (by construction) |
| Behavioral variability | Controlled by epsilon | Inherent (population diversity) | Controlled by coupling floor |
| Multi-condition memory | Q-table persists | Population persists | Reinforcement counts persist |
| Computational cost | Low (table lookup) | Moderate (population iteration) | Low (rate calculation) |
| Best for | Grid navigation, optimal policy | Matching, variability, dynamics | Matching, rate predictions |

## References

- Herrnstein, R. J. (1961). Relative and absolute strength of response as a function of frequency of reinforcement. *Journal of the Experimental Analysis of Behavior, 4*(3), 267–272.
- Killeen, P. R. (1994). Mathematical principles of reinforcement. *Behavioral and Brain Sciences, 17*(1), 105–135.
- McDowell, J. J. (2004). A computational model of selection by consequences. *Journal of the Experimental Analysis of Behavior, 81*(3), 297–317.
- Watkins, C. J. C. H., & Dayan, P. (1992). Q-learning. *Machine Learning, 8*(3), 279–292.
