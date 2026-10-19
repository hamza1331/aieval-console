"""Tests for advanced run filtering and export endpoints."""

import csv
import io

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.contract_service import ContractService
from app.services.evaluation_service import EvaluationService
from app.services.review_service import ReviewService


def test_runs_advanced_filtering_and_export(client: TestClient, db_session: Session):
    contract_service = ContractService(db_session)
    eval_service = EvaluationService(db_session)
    review_service = ReviewService(db_session)

    contract = contract_service.create_contract(
        name="Filter Test Contract",
        description="Contract for filter testing",
        checks=[
            {"type": "required_fields", "fields": ["user_id", "tier"]},
            {"type": "enum", "field": "tier", "allowed": ["free", "pro"]},
        ],
    )
    v_id = contract.versions[0].id

    # Run 1: passing
    r1 = eval_service.evaluate_and_persist(
        contract_version_id=v_id,
        output={"user_id": "u1", "tier": "pro"},
    )

    # Run 2: failing
    r2 = eval_service.evaluate_and_persist(
        contract_version_id=v_id,
        output={"user_id": "u2", "tier": "ultra_vip"},
    )
    review_service.update_review(run_id=r2.run_id, status="reviewed", note="Known tier expansion")

    # 1. Filter by review_status=reviewed
    res_reviewed = client.get("/api/v1/runs", params={"review_status": "reviewed"})
    assert res_reviewed.status_code == 200
    data_rev = res_reviewed.json()
    assert any(item["id"] == r2.run_id for item in data_rev["items"])
    assert not any(item["id"] == r1.run_id for item in data_rev["items"])

    # 2. Filter by failure_code=ENUM_MISMATCH
    res_code = client.get("/api/v1/runs", params={"failure_code": "ENUM_MISMATCH"})
    assert res_code.status_code == 200
    data_code = res_code.json()
    assert any(item["id"] == r2.run_id for item in data_code["items"])

    # 3. Export as CSV
    res_csv = client.get("/api/v1/runs/export", params={"format": "csv"})
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    reader = csv.reader(io.StringIO(res_csv.text))
    rows = list(reader)
    header = rows[0]
    assert "run_id" in header
    assert "contract_name" in header
    assert "status" in header
    assert len(rows) >= 3  # Header + at least 2 runs

    # 4. Export as JSON
    res_json = client.get("/api/v1/runs/export", params={"format": "json"})
    assert res_json.status_code == 200
    data_json = res_json.json()
    assert isinstance(data_json, list)
    assert any(item["id"] == r1.run_id for item in data_json)


def test_failure_code_filter_applies_before_pagination_and_counts_matches(
    client: TestClient,
    db_session: Session,
):
    contract = ContractService(db_session).create_contract(
        name="Failure Pagination",
        description=None,
        checks=[
            {"type": "required_fields", "fields": ["name"]},
            {"type": "enum", "field": "kind", "allowed": ["known"]},
        ],
    )
    eval_service = EvaluationService(db_session)
    version_id = contract.versions[0].id

    enum_runs = [
        eval_service.evaluate_and_persist(
            contract_version_id=version_id,
            output={"name": f"record-{idx}", "kind": "unknown"},
        ).run_id
        for idx in range(3)
    ]
    eval_service.evaluate_and_persist(
        contract_version_id=version_id,
        output={"kind": "known"},
    )

    response = client.get(
        "/api/v1/runs",
        params={
            "contract_id": contract.id,
            "failure_code": "enum_mismatch",
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] in enum_runs
