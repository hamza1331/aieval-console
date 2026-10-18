"""Tests for the /health endpoint (FR-14)."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["app_version"] == "0.1.0"
    assert "aieval_version" in data
    assert data["aieval_version"] is not None
