"""Shared fixtures for backend tests."""

import sys
import os

# Ensure backend package root is on sys.path so bare imports like
# ``from schedules.reinforcement import FR`` resolve correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture(autouse=True)
def numpy_seed():
    """Reset numpy RNG before every test for determinism."""
    np.random.seed(42)


@pytest.fixture
def client():
    """httpx AsyncClient wired to the FastAPI app (no live server needed)."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
