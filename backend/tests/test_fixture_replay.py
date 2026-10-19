"""Tests for fixture replay and import endpoints."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.run_repo import RunRepository
from app.services.contract_service import ContractService


def test_replay_passing_fixture(client: TestClient):
    fixture_path = (
        Path(__file__).resolve().parent.parent.parent
        / "fixtures"
        / "v1"
        / "support_ticket_valid.json"
    )
    fixture_dict = json.loads(fixture_path.read_text(encoding="utf-8"))

    payload = {"fixture": fixture_dict, "persist_run": False}
    response = client.post("/api/v1/fixtures/replay", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["actual_status"] == "passed"
    assert data["expected_status"] == "passed"
    assert data["parity_status"] == "match"
    assert data["matches_expected"] is True
    assert data["failures_count"] == 0


def test_replay_failing_fixture_matches_expected(client: TestClient):
    fixture_path = (
        Path(__file__).resolve().parent.parent.parent
        / "fixtures"
        / "v1"
        / "support_ticket_invalid.json"
    )
    fixture_dict = json.loads(fixture_path.read_text(encoding="utf-8"))

    payload = {"fixture": fixture_dict, "persist_run": False}
    response = client.post("/api/v1/fixtures/replay", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["actual_status"] == "failed"
    assert data["expected_status"] == "failed"
    assert data["parity_status"] == "match"
    assert data["matches_expected"] is True
    assert data["failures_count"] > 0


def test_replay_fixture_detects_regression(client: TestClient):
    # Fixture says expected: passed: true, but output is invalid!
    fixture_dict = {
        "name": "regression_test",
        "output": {"category": "invalid_value"},
        "checks": [
            {
                "type": "enum",
                "field": "category",
                "allowed": ["billing", "technical"],
            }
        ],
        "expected": {"passed": True, "failures": []},
    }

    payload = {"fixture": fixture_dict, "persist_run": False}
    response = client.post("/api/v1/fixtures/replay", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["actual_status"] == "failed"
    assert data["expected_status"] == "passed"
    assert data["parity_status"] == "regression"
    assert data["matches_expected"] is False
    assert len(data["differences"]) > 0


def test_import_fixture_as_contract(client: TestClient, db_session: Session):
    fixture_path = (
        Path(__file__).resolve().parent.parent.parent
        / "fixtures"
        / "v1"
        / "recruitment_screening_valid.json"
    )
    fixture_dict = json.loads(fixture_path.read_text(encoding="utf-8"))

    payload = {
        "fixture": fixture_dict,
        "contract_name": "Imported Recruitment Contract",
    }
    response = client.post("/api/v1/fixtures/import", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Imported Recruitment Contract"
    assert data["latest_version"] == 1
    assert data["status"] == "active"


def test_fixture_parity_includes_failure_paths(client: TestClient):
    fixture = {
        "output": {"category": "invalid"},
        "checks": [
            {
                "type": "enum",
                "field": "category",
                "allowed": ["valid"],
            }
        ],
        "expected": {
            "passed": False,
            "failures": [
                {"code": "ENUM_MISMATCH", "path": "wrong_path", "severity": "error"}
            ],
        },
    }

    response = client.post(
        "/api/v1/fixtures/replay",
        json={"fixture": fixture, "persist_run": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["parity_status"] == "divergence"
    assert data["matches_expected"] is False
    assert any("Missing expected failures" in item for item in data["differences"])


def test_fixture_parity_ignores_optional_failure_fields_when_omitted(client: TestClient):
    fixture = {
        "output": {"category": "invalid", "priority": "invalid"},
        "checks": [
            {
                "type": "enum",
                "field": "category",
                "allowed": ["valid"],
            },
            {
                "type": "enum",
                "field": "priority",
                "allowed": ["valid"],
            },
        ],
        "expected": {
            "passed": False,
            "failures": [
                {"code": "ENUM_MISMATCH"},
                {"code": "ENUM_MISMATCH", "path": "category"},
            ],
        },
    }

    response = client.post(
        "/api/v1/fixtures/replay",
        json={"fixture": fixture, "persist_run": False},
    )

    assert response.status_code == 200
    assert response.json()["parity_status"] == "match"
    assert response.json()["matches_expected"] is True


def test_fixture_parity_checks_explicit_null_path(client: TestClient):
    fixture = {
        "output": {"category": "invalid"},
        "checks": [
            {
                "type": "enum",
                "field": "category",
                "allowed": ["valid"],
            }
        ],
        "expected": {
            "passed": False,
            "failures": [{"code": "ENUM_MISMATCH", "path": None}],
        },
    }

    response = client.post(
        "/api/v1/fixtures/replay",
        json={"fixture": fixture, "persist_run": False},
    )

    assert response.status_code == 200
    assert response.json()["parity_status"] == "divergence"


def test_fixture_validation_rejects_malformed_expected_failure(client: TestClient):
    response = client.post(
        "/api/v1/fixtures/validate",
        json={
            "fixture": {
                "output": {},
                "checks": [{"type": "valid_json"}],
                "expected": {"passed": False, "failures": [{"path": 3}]},
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["error"].lower().endswith("must be a string.")


def test_fixture_replay_persists_exact_replayed_result(
    client: TestClient,
    db_session: Session,
):
    checks = [{"type": "enum", "field": "category", "allowed": ["valid"]}]
    contract = ContractService(db_session).create_contract(
        name="Fixture Replay Persistence",
        description=None,
        checks=checks,
    )
    fixture = {
        "output": {"category": "invalid"},
        "checks": checks,
        "expected": {
            "passed": False,
            "failures": [
                {"code": "ENUM_MISMATCH", "path": "category", "severity": "error"}
            ],
        },
    }

    response = client.post(
        "/api/v1/fixtures/replay",
        json={
            "fixture": fixture,
            "persist_run": True,
            "contract_id": contract.id,
        },
    )

    assert response.status_code == 200
    run_id = response.json()["run_id"]
    run = RunRepository(db_session).get_by_id(run_id)
    assert run is not None
    assert run.output_json == fixture["output"]
    assert run.result_json["failures"][0]["path"] == "category"
    assert response.json()["failures"][0]["path"] == "category"
