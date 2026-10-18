"""Pytest fixtures for API testing."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture reusing the configured FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client

