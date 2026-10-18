"""Tests for POST /api/v1/evaluations endpoint and run persistence (FR-04, FR-07)."""

from fastapi.testclient import TestClient

APPENDIX_A_CONTRACT = {
    "name": "Support ticket classification",
    "description": "Validate structured output from a ticket classifier",
    "checks": [
        {
            "type": "required_fields",
            "fields": ["category", "priority", "summary"],
        },
        {
            "type": "enum",
            "field": "category",
            "allowed": ["billing", "technical", "account", "other"],
        },
        {
            "type": "enum",
            "field": "priority",
            "allowed": ["low", "normal", "high", "urgent"],
        },
        {
            "type": "max_length",
            "field": "summary",
            "max": 300,
        },
    ],
}


def test_evaluation_inline_contract_valid_passes(client: TestClient) -> None:
    payload = {
        "contract": APPENDIX_A_CONTRACT,
        "input": {"task": "classify_support_ticket"},
        "output": {
            "category": "billing",
            "priority": "urgent",
            "summary": "Customer billing card declined on annual renewal",
        },
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "passed"
    assert "run_id" in data
    assert data["duration_ms"] >= 0
    assert data["summary"]["total_checks"] == 4
    assert data["summary"]["passed_checks"] == 4
    assert data["summary"]["failed_checks"] == 0
    assert len(data["failures"]) == 0


def test_evaluation_persists_run_with_contract_version_id(client: TestClient) -> None:
    # 1. Create a contract and get its version ID
    contract_res = client.post(
        "/api/v1/contracts",
        json={
            "name": "Support Ticket Suite",
            "checks": APPENDIX_A_CONTRACT["checks"],
        },
    )
    assert contract_res.status_code == 201
    version_id = contract_res.json()["versions"][0]["id"]

    # 2. Evaluate output against version ID
    eval_payload = {
        "contract_version_id": version_id,
        "input": {"ticket_id": "TICK-101"},
        "output": {
            "category": "billing",
            "priority": "super_urgent_now",  # Invalid enum
            "summary": "Urgent customer ticket",
        },
    }
    eval_res = client.post("/api/v1/evaluations", json=eval_payload)
    assert eval_res.status_code == 200

    data = eval_res.json()
    assert data["status"] == "failed"
    assert data["contract_version"] == 1
    run_id = data["run_id"]
    assert run_id is not None

    # 3. Verify run was persisted in the database
    run_res = client.get(f"/api/v1/runs/{run_id}")
    assert run_res.status_code == 200
    run_detail = run_res.json()
    assert run_detail["id"] == run_id
    assert run_detail["status"] == "failed"
    assert run_detail["contract_version_id"] == version_id
    assert run_detail["input_json"]["ticket_id"] == "TICK-101"
    assert run_detail["review"]["status"] == "unreviewed"


def test_evaluation_with_contract_id_resolves_latest_version(client: TestClient) -> None:
    # Create contract
    contract_res = client.post(
        "/api/v1/contracts",
        json={
            "name": "Latest Version Test",
            "checks": [{"type": "required_fields", "fields": ["field_a"]}],
        },
    )
    contract_id = contract_res.json()["id"]

    # Add version 2
    client.post(
        f"/api/v1/contracts/{contract_id}/versions",
        json={"checks": [{"type": "required_fields", "fields": ["field_a", "field_b"]}]},
    )

    # Evaluate using contract_id
    eval_res = client.post(
        "/api/v1/evaluations",
        json={
            "contract_id": contract_id,
            "output": {"field_a": 1, "field_b": 2},
        },
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["status"] == "passed"
    assert eval_res.json()["contract_version"] == 2


def test_evaluation_contract_version_id_not_found(client: TestClient) -> None:
    payload = {
        "contract_version_id": "non-existent-version-id",
        "output": {"test": "value"},
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_evaluation_missing_contract_specification(client: TestClient) -> None:
    payload = {
        "output": {"test": "value"},
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 400
    assert "must specify" in response.json()["detail"].lower()


def test_evaluation_unsupported_check_type_returns_422(client: TestClient) -> None:
    payload = {
        "contract": {
            "name": "Invalid Contract",
            "checks": [
                {"type": "non_existent_check_type", "param": 123},
            ],
        },
        "output": {"data": "test"},
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 422


def test_payload_limit_middleware_rejects_oversized_payload(client: TestClient) -> None:
    oversized_summary = "a" * (600 * 1024)
    payload = {
        "contract": APPENDIX_A_CONTRACT,
        "output": {"summary": oversized_summary},
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 413
    assert "exceeds maximum allowed" in response.json()["detail"]
