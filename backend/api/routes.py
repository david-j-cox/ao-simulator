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
        gc = req.grid_config
        if not gc or not gc.levers:
            raise HTTPException(400, "grid_chamber requires grid_config with levers")
        levers = [
            {
                "pos": (lc.row, lc.col),
                "schedule": create_schedule(lc.schedule.type, lc.schedule.value),
                "magnitude": lc.magnitude,
            }
            for lc in gc.levers
        ]
        return GridChamberEnvironment(
            rows=gc.rows,
            cols=gc.cols,
            levers=levers,
            max_steps=req.max_steps,
            start_pos=(gc.start_row, gc.start_col),
        )
    else:
        raise HTTPException(400, f"Unknown environment: {req.environment}")


def _build_environment_for_condition(req: SimulationRequest, condition):
    """Factory: create the environment from first condition + grid_config."""
    if req.environment == "two_choice":
        if not condition.schedule_a or not condition.schedule_b:
            raise HTTPException(400, f"Condition '{condition.label}': two_choice requires schedule_a and schedule_b")
        return TwoChoiceEnvironment(
            schedule_a=create_schedule(condition.schedule_a.type, condition.schedule_a.value),
            schedule_b=create_schedule(condition.schedule_b.type, condition.schedule_b.value),
            max_steps=condition.max_steps,
        )
    elif req.environment == "grid_chamber":
        gc = req.grid_config
        if not gc or not gc.levers:
            raise HTTPException(400, f"Condition '{condition.label}': grid_chamber requires grid_config with levers")
        if not condition.lever_schedules:
            raise HTTPException(400, f"Condition '{condition.label}': grid_chamber requires lever_schedules")
        # Positions come from grid_config.levers; schedules+magnitudes from condition
        levers = []
        for i, lc in enumerate(gc.levers):
            ls = condition.lever_schedules[i]
            levers.append({
                "pos": (lc.row, lc.col),
                "schedule": create_schedule(ls.schedule.type, ls.schedule.value),
                "magnitude": ls.magnitude,
            })
        return GridChamberEnvironment(
            rows=gc.rows,
            cols=gc.cols,
            levers=levers,
            max_steps=condition.max_steps,
            start_pos=(gc.start_row, gc.start_col),
        )
    else:
        raise HTTPException(400, f"Unknown environment: {req.environment}")


def _swap_env_schedules(env, cond_dict):
    """Swap schedules and max_steps on an existing environment for a new condition."""
    env.max_steps = cond_dict["max_steps"]

    if isinstance(env, TwoChoiceEnvironment):
        env.schedule_a = create_schedule(cond_dict["schedule_a"]["type"], cond_dict["schedule_a"]["value"])
        env.schedule_b = create_schedule(cond_dict["schedule_b"]["type"], cond_dict["schedule_b"]["value"])
    elif isinstance(env, GridChamberEnvironment):
        for i, ls in enumerate(cond_dict["lever_schedules"]):
            env.levers[i]["schedule"] = create_schedule(ls["schedule"]["type"], ls["schedule"]["value"])
            env.levers[i]["magnitude"] = ls["magnitude"]


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
        elif req.environment == "grid_chamber" and req.grid_config and req.grid_config.levers:
            sched_type = req.grid_config.levers[0].schedule.type
        # Fall back to first condition's schedule when top-level is None
        elif req.conditions:
            c0 = req.conditions[0]
            if req.environment == "two_choice" and c0.schedule_a:
                sched_type = c0.schedule_a.type
            elif req.environment == "grid_chamber" and c0.lever_schedules:
                sched_type = c0.lever_schedules[0].schedule.type
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
    if req.conditions:
        # Multi-condition path
        first_cond = req.conditions[0]
        env = _build_environment_for_condition(req, first_cond)
        agent = _build_agent(req)
        runner = SimulationRunner(agent, env)

        # Build condition dicts for the runner
        cond_dicts = []
        for c in req.conditions:
            d = {"label": c.label, "max_steps": c.max_steps}
            if req.environment == "two_choice":
                d["schedule_a"] = {"type": c.schedule_a.type, "value": c.schedule_a.value}
                d["schedule_b"] = {"type": c.schedule_b.type, "value": c.schedule_b.value}
            else:
                d["lever_schedules"] = [
                    {"schedule": {"type": ls.schedule.type, "value": ls.schedule.value}, "magnitude": ls.magnitude}
                    for ls in c.lever_schedules
                ]
            cond_dicts.append(d)

        return runner.run_multi_condition(
            conditions=cond_dicts,
            swap_env_fn=_swap_env_schedules,
            seed=req.seed,
        )
    else:
        # Single-condition path
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
        condition_summaries=result.condition_summaries,
    )


@router.post("/simulate/csv")
async def simulate_csv(req: SimulationRequest):
    """Run a simulation and return results as CSV."""
    result = _run_simulation(req)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "step", "state", "action", "reinforced", "schedule_id", "condition", "reinforcement_magnitude",
    ])
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
        "condition_summaries": result.condition_summaries,
    }
    content = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=simulation_results.json"},
    )
