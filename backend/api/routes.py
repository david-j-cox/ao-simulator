"""API routes for simulation endpoints."""

import csv
import io
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import SimulationRequest, SimulationResponse
from schedules.reinforcement import create_schedule
from environments.two_choice import TwoChoiceEnvironment
from environments.grid_chamber import GridChamberEnvironment
from agents.q_learning import QLearningAgent
from agents.etbd import ETBDAgent
from agents.mpr import MPRAgent
from simulation.runner import SimulationRunner

router = APIRouter(prefix="/api")


def _build_environment(req: SimulationRequest):
    """Factory: create the environment from request config."""
    if req.environment == "two_choice":
        if not req.schedule_a or not req.schedule_b:
            raise HTTPException(400, "two_choice requires schedule_a and schedule_b")
        return TwoChoiceEnvironment(
            schedule_a=create_schedule(req.schedule_a.type, req.schedule_a.value),
            schedule_b=create_schedule(req.schedule_b.type, req.schedule_b.value),
            max_steps=req.max_steps,
        )
    elif req.environment == "grid_chamber":
        if not req.schedule:
            raise HTTPException(400, "grid_chamber requires schedule")
        gc = req.grid_config
        kwargs = {}
        if gc:
            kwargs = dict(
                rows=gc.rows, cols=gc.cols,
                lever_pos=(gc.lever_row, gc.lever_col),
                start_pos=(gc.start_row, gc.start_col),
            )
        return GridChamberEnvironment(
            schedule=create_schedule(req.schedule.type, req.schedule.value),
            max_steps=req.max_steps,
            **kwargs,
        )
    else:
        raise HTTPException(400, f"Unknown environment: {req.environment}")


def _build_agent(req: SimulationRequest):
    """Factory: create the agent from request config."""
    if req.algorithm == "q_learning":
        p = req.q_learning_params or {}
        if hasattr(p, "model_dump"):
            p = p.model_dump()
        use_history = req.environment == "two_choice"
        return QLearningAgent(
            alpha=p.get("alpha", 0.1),
            gamma=p.get("gamma", 0.9),
            epsilon=p.get("epsilon", 0.1),
            history_window=p.get("history_window", 3),
            use_history_state=use_history,
        )
    elif req.algorithm == "etbd":
        p = req.etbd_params or {}
        if hasattr(p, "model_dump"):
            p = p.model_dump()
        return ETBDAgent(
            population_size=p.get("population_size", 100),
            mutation_rate=p.get("mutation_rate", 0.1),
            fitness_decay=p.get("fitness_decay", 0.95),
            environment_type=req.environment,
        )
    elif req.algorithm == "mpr":
        p = req.mpr_params or {}
        if hasattr(p, "model_dump"):
            p = p.model_dump()
        # Determine schedule type from the schedules configured
        sched_type = "VI"
        if req.environment == "two_choice" and req.schedule_a:
            sched_type = req.schedule_a.type
        elif req.environment == "grid_chamber" and req.schedule:
            sched_type = req.schedule.type
        return MPRAgent(
            environment_type=req.environment,
            initial_arousal=p.get("initial_arousal", 1.0),
            activation_decay=p.get("activation_decay", 0.95),
            coupling_floor=p.get("coupling_floor", 0.01),
            temperature=p.get("temperature", 1.0),
            schedule_type=sched_type,
        )
    else:
        raise HTTPException(400, f"Unknown algorithm: {req.algorithm}")


def _run_simulation(req: SimulationRequest):
    """Build components and run simulation."""
    env = _build_environment(req)
    agent = _build_agent(req)
    runner = SimulationRunner(agent, env)
    return runner.run(seed=req.seed)


@router.post("/simulate", response_model=SimulationResponse)
async def simulate(req: SimulationRequest):
    """Run a simulation and return full results as JSON."""
    result = _run_simulation(req)
    return SimulationResponse(
        config=result.config,
        summary=result.summary,
        steps=result.steps,
    )


@router.post("/simulate/csv")
async def simulate_csv(req: SimulationRequest):
    """Run a simulation and return results as CSV."""
    result = _run_simulation(req)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["step", "state", "action", "reinforced", "schedule_id"])
    writer.writeheader()
    for step in result.steps:
        writer.writerow(step)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=simulation_results.csv"},
    )


@router.post("/simulate/json")
async def simulate_json(req: SimulationRequest):
    """Run a simulation and return results as downloadable JSON."""
    result = _run_simulation(req)
    data = {
        "config": result.config,
        "summary": result.summary,
        "steps": result.steps,
    }
    content = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=simulation_results.json"},
    )
