"""Tests for POST /api/v1/evaluations endpoint (FR-04, FR-05, FR-06)."""

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


def test_evaluation_inline_contract_invalid_enum(client: TestClient) -> None:
    payload = {
        "contract": APPENDIX_A_CONTRACT,
        "input": {"task": "classify_support_ticket"},
        "output": {
            "category": "billing",
            "priority": "super_urgent_now",  # Invalid enum
            "summary": "Urgent customer ticket",
        },
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "failed"
    assert data["summary"]["failed_checks"] >= 1
    assert len(data["failures"]) >= 1

    enum_failure = next((f for f in data["failures"] if f["code"] == "ENUM_MISMATCH"), None)
    assert enum_failure is not None
    assert enum_failure["path"] == "priority"
    assert enum_failure["severity"] == "error"


def test_evaluation_contract_version_id_lookup(client: TestClient) -> None:
    payload = {
        "contract_version_id": "demo-support-ticket-v1",
        "output": {
            "category": "technical",
            "priority": "high",
            "summary": "API endpoint throwing 500 error on checkout",
        },
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "passed"
    assert data["contract_version"] == 1


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
    assert "either 'contract_version_id' or inline 'contract'" in response.json()["detail"]


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
    assert "Invalid contract check specification" in response.json()["detail"]


def test_payload_limit_middleware_rejects_oversized_payload(client: TestClient) -> None:
    # 600 KB payload exceeds default 500 KB limit
    oversized_summary = "a" * (600 * 1024)
    payload = {
        "contract": APPENDIX_A_CONTRACT,
        "output": {"summary": oversized_summary},
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 413
    assert "exceeds maximum allowed" in response.json()["detail"]
