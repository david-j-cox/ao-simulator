"""Pydantic request/response models for the API."""

from pydantic import BaseModel, Field
from typing import Optional


class ScheduleConfig(BaseModel):
    type: str = Field(..., description="Schedule type: FR, VR, FI, or VI")
    value: int = Field(..., gt=0, description="Schedule parameter value")


class QLearningParams(BaseModel):
    alpha: float = Field(0.1, ge=0, le=1, description="Learning rate")
    gamma: float = Field(0.9, ge=0, le=1, description="Discount factor")
    epsilon: float = Field(0.1, ge=0, le=1, description="Exploration rate")
    history_window: int = Field(3, ge=1, description="State history window size")


class ETBDParams(BaseModel):
    population_size: int = Field(100, ge=10, description="Population size")
    mutation_rate: float = Field(0.1, ge=0, le=1, description="Bit-flip mutation rate")
    fitness_decay: float = Field(0.95, ge=0, le=1, description="Fitness decay parameter")


class MPRParams(BaseModel):
    initial_arousal: float = Field(1.0, gt=0, description="Initial arousal parameter (a)")
    activation_decay: float = Field(0.95, gt=0, description="Activation decay parameter (b)")
    coupling_floor: float = Field(0.01, ge=0, description="Minimum coupling value")
    temperature: float = Field(1.0, gt=0, description="Softmax temperature (grid only)")


class GridConfig(BaseModel):
    rows: int = Field(5, ge=2, le=20, description="Grid rows")
    cols: int = Field(5, ge=2, le=20, description="Grid columns")
    lever_row: int = Field(2, ge=0, description="Lever row position")
    lever_col: int = Field(2, ge=0, description="Lever column position")
    start_row: int = Field(0, ge=0, description="Start row position")
    start_col: int = Field(0, ge=0, description="Start column position")


class ConditionConfig(BaseModel):
    label: str = Field(..., description="Condition label (e.g. 'Baseline', 'Extinction')")
    max_steps: int = Field(1000, ge=1, le=100000, description="Steps for this condition")
    schedule_a: Optional[ScheduleConfig] = Field(None, description="Schedule A (two-choice)")
    schedule_b: Optional[ScheduleConfig] = Field(None, description="Schedule B (two-choice)")
    schedule: Optional[ScheduleConfig] = Field(None, description="Lever schedule (grid)")


class SimulationRequest(BaseModel):
    environment: str = Field(..., description="Environment type: two_choice or grid_chamber")
    algorithm: str = Field(..., description="Algorithm: q_learning, etbd, or mpr")
    max_steps: int = Field(1000, ge=1, le=100000, description="Maximum simulation steps")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    # Schedule configs
    schedule_a: Optional[ScheduleConfig] = Field(None, description="Schedule A (two-choice)")
    schedule_b: Optional[ScheduleConfig] = Field(None, description="Schedule B (two-choice)")
    schedule: Optional[ScheduleConfig] = Field(None, description="Lever schedule (grid)")

    # Algorithm params (only one should be set based on algorithm choice)
    q_learning_params: Optional[QLearningParams] = None
    etbd_params: Optional[ETBDParams] = None
    mpr_params: Optional[MPRParams] = None

    # Grid config (only for grid_chamber)
    grid_config: Optional[GridConfig] = None

    # Multi-condition experiment (overrides top-level schedule/max_steps when non-empty)
    conditions: Optional[list[ConditionConfig]] = Field(
        None, max_length=6,
        description="Up to 6 conditions for multi-phase experiments"
    )


class StepData(BaseModel):
    step: int
    state: str
    action: str
    reinforced: bool
    schedule_id: str
    condition: int = Field(1, description="Condition number (1-indexed)")


class ConditionSummary(BaseModel):
    condition: int
    label: str
    start_step: int
    end_step: int
    total_steps: int
    total_reinforcements: int
    reinforcement_rate: float
    action_counts: dict[str, int]


class SimulationResponse(BaseModel):
    config: dict
    summary: dict
    steps: list[StepData]
    condition_summaries: list[ConditionSummary] = Field(default_factory=list)
