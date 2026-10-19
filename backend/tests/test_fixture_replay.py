"""Tests for fixture replay and import endpoints."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


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

