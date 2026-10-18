"""Tests for GET /api/v1/overview endpoint (FR-11)."""

from fastapi.testclient import TestClient

CHECKS = [{"type": "required_fields", "fields": ["status"]}]


def test_overview_statistics_and_recent_runs(client: TestClient) -> None:
    # 1. Create a contract and versions
    c1_res = client.post(
        "/api/v1/contracts",
        json={"name": "Overview Contract 1", "checks": CHECKS},
    )
    v1_id = c1_res.json()["versions"][0]["id"]

    # 2. Submit runs
    # Run 1: Pass
    client.post(
        "/api/v1/evaluations",
        json={"contract_version_id": v1_id, "output": {"status": "ok"}},
    )
    # Run 2: Fail (unreviewed)
    client.post(
        "/api/v1/evaluations",
        json={"contract_version_id": v1_id, "output": {}},
    )

    # 3. Request overview
    res = client.get("/api/v1/overview")
    assert res.status_code == 200
    data = res.json()

    assert data["total_contracts"] >= 1
    assert data["active_contracts"] >= 1
    assert data["total_runs"] >= 2
    assert data["passed_runs"] >= 1
    assert data["failed_runs"] >= 1
    assert 0.0 <= data["pass_rate"] <= 100.0
    assert data["unreviewed_failures"] >= 1
    assert len(data["recent_runs"]) >= 2
    assert data["recent_runs"][0]["contract_name"] == "Overview Contract 1"
