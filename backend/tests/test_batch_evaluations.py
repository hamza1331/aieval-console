"""Tests for batch evaluation endpoint POST /api/v1/evaluations/batch."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.contract_service import ContractService


def test_batch_evaluation_with_inline_contract(client: TestClient):
    inline_contract = {
        "name": "Batch Test Contract",
        "checks": [
            {"type": "required_fields", "fields": ["id", "status"]},
            {"type": "enum", "field": "status", "allowed": ["active", "pending"]},
        ],
    }

    payload = {
        "contract": inline_contract,
        "items": [
            {"item_id": "item-1", "output": {"id": "1", "status": "active"}},
            {"item_id": "item-2", "output": {"id": "2", "status": "pending"}},
            {"item_id": "item-3", "output": {"id": "3", "status": "invalid_status"}},
            {"item_id": "item-4", "output": {"status": "active"}},  # missing id
        ],
    }

    response = client.post("/api/v1/evaluations/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total_items"] == 4
    assert data["passed_count"] == 2
    assert data["failed_count"] == 2
    assert data["pass_rate"] == 50.0
    assert len(data["results"]) == 4

    # Item 1 and 2 passed
    assert data["results"][0]["status"] == "passed"
    assert data["results"][1]["status"] == "passed"

    # Item 3 failed enum
    assert data["results"][2]["status"] == "failed"
    assert any(f["code"] == "ENUM_MISMATCH" for f in data["results"][2]["failures"])

    # Item 4 failed required_fields
    assert data["results"][3]["status"] == "failed"
    assert any(f["code"] == "MISSING_REQUIRED_FIELD" for f in data["results"][3]["failures"])


def test_batch_evaluation_with_stored_contract(client: TestClient, db_session: Session):
    service = ContractService(db_session)
    contract = service.create_contract(
        name="Stored Batch Contract",
        description="Testing batch with stored contract",
        checks=[{"type": "required_fields", "fields": ["code"]}],
    )

    payload = {
        "contract_id": contract.id,
        "items": [
            {"item_id": "a", "output": {"code": "XYZ"}},
            {"item_id": "b", "output": {"code": "ABC"}},
        ],
    }

    response = client.post("/api/v1/evaluations/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["passed_count"] == 2
    assert data["failed_count"] == 0
    assert data["pass_rate"] == 100.0


def test_batch_evaluation_missing_contract_returns_400(client: TestClient):
    payload = {
        "items": [{"output": {"key": "val"}}],
    }
    response = client.post("/api/v1/evaluations/batch", json=payload)
    assert response.status_code == 400

