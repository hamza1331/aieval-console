"""Tests for contract version diff endpoint GET /api/v1/contracts/{id}/diff."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.contract_service import ContractService


def test_contract_diff_versions(client: TestClient, db_session: Session):
    service = ContractService(db_session)
    contract = service.create_contract(
        name="Diff Test Contract",
        description="Testing diffing",
        checks=[
            {"type": "required_fields", "fields": ["id", "status"]},
            {"type": "enum", "field": "status", "allowed": ["active", "pending"]},
        ],
    )

    # Create v2 with modified enum allowed values, removed required_fields, and added numeric_range
    service.create_new_version(
        contract_id=contract.id,
        checks=[
            {"type": "enum", "field": "status", "allowed": ["active", "pending", "archived"]},
            {"type": "numeric_range", "field": "score", "min": 0, "max": 100},
        ],
    )

    response = client.get(
        f"/api/v1/contracts/{contract.id}/diff",
        params={"from_version": 1, "to_version": 2},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["contract_id"] == contract.id
    assert data["from_version"] == 1
    assert data["to_version"] == 2
    assert data["added_count"] == 1  # numeric_range added
    assert data["removed_count"] == 1  # required_fields removed
    assert data["modified_count"] == 1  # enum modified

    # Find modified item
    modified_items = [c for c in data["checks"] if c["change_type"] == "modified"]
    assert len(modified_items) == 1
    assert modified_items[0]["check_type"] == "enum"
    assert any("allowed" in detail for detail in modified_items[0]["details"])


def test_contract_diff_version_not_found(client: TestClient, db_session: Session):
    service = ContractService(db_session)
    contract = service.create_contract(
        name="Single Version Contract",
        description="Only v1",
        checks=[{"type": "required_fields", "fields": ["id"]}],
    )

    response = client.get(
        f"/api/v1/contracts/{contract.id}/diff",
        params={"from_version": 1, "to_version": 99},
    )
    assert response.status_code == 404
