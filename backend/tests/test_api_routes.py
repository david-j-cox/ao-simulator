"""Tests for API routes."""

import csv
import io
import json
import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _two_choice_req(algo="q_learning", seed=42, max_steps=50):
    req = {
        "environment": "two_choice",
        "algorithm": algo,
        "max_steps": max_steps,
        "seed": seed,
        "schedule_a": {"type": "FR", "value": 5},
        "schedule_b": {"type": "FR", "value": 5},
    }
    if algo == "mpr":
        req["mpr_params"] = {"initial_arousal": 1.0, "activation_decay": 0.95,
                              "coupling_floor": 0.01, "temperature": 1.0}
    return req


def _grid_req(algo="q_learning", seed=42, max_steps=50):
    req = {
        "environment": "grid_chamber",
        "algorithm": algo,
        "max_steps": max_steps,
        "seed": seed,
        "schedule": {"type": "FR", "value": 5},
        "grid_config": {"rows": 5, "cols": 5, "lever_row": 2, "lever_col": 2,
                        "start_row": 0, "start_col": 0},
    }
    if algo == "mpr":
        req["mpr_params"] = {"initial_arousal": 1.0, "activation_decay": 0.95,
                              "coupling_floor": 0.01, "temperature": 1.0}
    return req


# ── All 6 combos return 200 ────────────────────────────────────────

class TestSimulateEndpoint:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("algo", ["q_learning", "etbd", "mpr"])
    async def test_two_choice_200(self, client, algo):
        resp = await client.post("/api/simulate", json=_two_choice_req(algo))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize("algo", ["q_learning", "etbd", "mpr"])
    async def test_grid_200(self, client, algo):
        resp = await client.post("/api/simulate", json=_grid_req(algo))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_seeded_reproducibility(self, client):
        r1 = await client.post("/api/simulate", json=_two_choice_req(seed=99))
        r2 = await client.post("/api/simulate", json=_two_choice_req(seed=99))
        assert r1.json()["steps"] == r2.json()["steps"]

    @pytest.mark.asyncio
    async def test_step_count(self, client):
        resp = await client.post("/api/simulate", json=_two_choice_req(max_steps=30))
        data = resp.json()
        assert len(data["steps"]) == 30

    @pytest.mark.asyncio
    async def test_response_structure(self, client):
        resp = await client.post("/api/simulate", json=_two_choice_req())
        data = resp.json()
        assert "config" in data
        assert "summary" in data
        assert "steps" in data
        assert "condition_summaries" in data

    @pytest.mark.asyncio
    async def test_multi_condition(self, client):
        req = {
            "environment": "two_choice",
            "algorithm": "q_learning",
            "max_steps": 100,
            "seed": 42,
            "conditions": [
                {"label": "A", "max_steps": 30,
                 "schedule_a": {"type": "FR", "value": 5},
                 "schedule_b": {"type": "FR", "value": 5}},
                {"label": "B", "max_steps": 20,
                 "schedule_a": {"type": "VI", "value": 10},
                 "schedule_b": {"type": "VI", "value": 10}},
            ],
        }
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["condition_summaries"]) == 2
        assert data["condition_summaries"][0]["label"] == "A"
        assert data["condition_summaries"][1]["label"] == "B"

    @pytest.mark.asyncio
    async def test_multi_condition_grid(self, client):
        req = {
            "environment": "grid_chamber",
            "algorithm": "q_learning",
            "max_steps": 100,
            "seed": 42,
            "grid_config": {"rows": 3, "cols": 3, "lever_row": 1, "lever_col": 1,
                            "start_row": 0, "start_col": 0},
            "conditions": [
                {"label": "C1", "max_steps": 20,
                 "schedule": {"type": "FR", "value": 3}},
                {"label": "C2", "max_steps": 20,
                 "schedule": {"type": "VI", "value": 5}},
            ],
        }
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 200


# ── CSV endpoint ────────────────────────────────────────────────────

class TestCSVEndpoint:
    @pytest.mark.asyncio
    async def test_content_type(self, client):
        resp = await client.post("/api/simulate/csv", json=_two_choice_req())
        assert "text/csv" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_header_row(self, client):
        resp = await client.post("/api/simulate/csv", json=_two_choice_req())
        lines = resp.text.strip().split("\n")
        header = lines[0]
        assert "step" in header
        assert "action" in header
        assert "reinforced" in header

    @pytest.mark.asyncio
    async def test_row_count(self, client):
        resp = await client.post("/api/simulate/csv", json=_two_choice_req(max_steps=20))
        lines = resp.text.strip().split("\n")
        assert len(lines) == 21  # header + 20 data rows

    @pytest.mark.asyncio
    async def test_parseable(self, client):
        resp = await client.post("/api/simulate/csv", json=_two_choice_req())
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 50
        assert "step" in rows[0]


# ── JSON download endpoint ──────────────────────────────────────────

class TestJSONEndpoint:
    @pytest.mark.asyncio
    async def test_content_type(self, client):
        resp = await client.post("/api/simulate/json", json=_two_choice_req())
        assert "application/json" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_structure(self, client):
        resp = await client.post("/api/simulate/json", json=_two_choice_req())
        data = resp.json()
        assert "config" in data
        assert "summary" in data
        assert "steps" in data

    @pytest.mark.asyncio
    async def test_matches_simulate(self, client):
        req = _two_choice_req(seed=42)
        r_sim = await client.post("/api/simulate", json=req)
        r_json = await client.post("/api/simulate/json", json=req)
        sim_data = r_sim.json()
        json_data = r_json.json()
        assert len(sim_data["steps"]) == len(json_data["steps"])


# ── Error handling ──────────────────────────────────────────────────

class TestErrors:
    @pytest.mark.asyncio
    async def test_unknown_env(self, client):
        req = {"environment": "unknown", "algorithm": "q_learning",
               "schedule_a": {"type": "FR", "value": 5},
               "schedule_b": {"type": "FR", "value": 5}}
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_unknown_algo(self, client):
        req = {"environment": "two_choice", "algorithm": "unknown",
               "schedule_a": {"type": "FR", "value": 5},
               "schedule_b": {"type": "FR", "value": 5}}
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_schedules(self, client):
        req = {"environment": "two_choice", "algorithm": "q_learning"}
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_schedule_type(self, client):
        req = {"environment": "two_choice", "algorithm": "q_learning",
               "schedule_a": {"type": "INVALID", "value": 5},
               "schedule_b": {"type": "FR", "value": 5}}
        # create_schedule raises ValueError for unknown types (unhandled → 500)
        with pytest.raises(ValueError, match="Unknown schedule type"):
            await client.post("/api/simulate", json=req)

    @pytest.mark.asyncio
    async def test_missing_fields(self, client):
        resp = await client.post("/api/simulate", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_values(self, client):
        req = {"environment": "two_choice", "algorithm": "q_learning",
               "max_steps": -1}
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 422


# ── Root endpoint ───────────────────────────────────────────────────

class TestRootEndpoint:
    @pytest.mark.asyncio
    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "AO Simulator API"


# ── Factory function behavior ──────────────────────────────────────

class TestFactoryBehavior:
    @pytest.mark.asyncio
    async def test_grid_missing_schedule(self, client):
        req = {"environment": "grid_chamber", "algorithm": "q_learning"}
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_two_choice_missing_schedule_b(self, client):
        req = {"environment": "two_choice", "algorithm": "q_learning",
               "schedule_a": {"type": "FR", "value": 5}}
        resp = await client.post("/api/simulate", json=req)
        assert resp.status_code == 400
