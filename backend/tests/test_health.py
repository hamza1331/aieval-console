"""Tests for the /health endpoint (FR-14)."""

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["app_version"] == "0.1.0"
    assert "aieval_version" in data
    assert data["aieval_version"] is not None


def test_health_endpoint_reports_database_unavailable(
    client: TestClient, db_session, monkeypatch
) -> None:
    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(db_session, "execute", fail_query)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not ready."
