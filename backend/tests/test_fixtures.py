"""Tests for fixture export and validation endpoints (FR-10, FR-16)."""

from fastapi.testclient import TestClient

CHECKS = [
    {"type": "required_fields", "fields": ["ticket_type", "priority"]},
    {"type": "enum", "field": "priority", "allowed": ["low", "high"]},
]


def test_export_fixture_and_download(client: TestClient) -> None:
    # 1. Create contract and execute failing run
    contract_res = client.post(
        "/api/v1/contracts",
        json={"name": "Fixture Export Contract", "checks": CHECKS},
    )
    version_id = contract_res.json()["versions"][0]["id"]

    eval_res = client.post(
        "/api/v1/evaluations",
        json={
            "contract_version_id": version_id,
            "input": {"id": 123},
            "output": {"ticket_type": "bug", "priority": "emergency"},
        },
    )
    run_id = eval_res.json()["run_id"]

    # 2. Export fixture (JSON response)
    fix_res = client.get(f"/api/v1/runs/{run_id}/fixture")
    assert fix_res.status_code == 200
    fixture = fix_res.json()

    assert fixture["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert fixture["name"].startswith("golden_fixture_")
    assert fixture["context"]["input"]["id"] == 123
    assert fixture["output"]["priority"] == "emergency"
    assert len(fixture["checks"]) == 2
    assert fixture["expected"]["passed"] is False
    assert len(fixture["expected"]["failures"]) == 1
    assert fixture["expected"]["failures"][0]["code"] == "ENUM_MISMATCH"

    # 3. Export fixture with download attachment
    dl_res = client.get(f"/api/v1/runs/{run_id}/fixture?download=true")
    assert dl_res.status_code == 200
    assert "attachment; filename=" in dl_res.headers.get("content-disposition", "")


def test_export_fixture_not_found(client: TestClient) -> None:
    res = client.get("/api/v1/runs/non-existent-uuid/fixture")
    assert res.status_code == 404


def test_validate_fixture_success_and_errors(client: TestClient) -> None:
    # Valid fixture
    valid_payload = {
        "fixture": {
            "output": {"code": 1},
            "checks": [{"type": "required_fields", "fields": ["code"]}],
            "expected": {"passed": True},
        }
    }
    v_res = client.post("/api/v1/fixtures/validate", json=valid_payload)
    assert v_res.status_code == 200
    assert v_res.json()["valid"] is True
    assert v_res.json()["checks_count"] == 1

    # Missing output
    invalid_no_output = {
        "fixture": {
            "checks": [{"type": "valid_json"}],
        }
    }
    inv_res = client.post("/api/v1/fixtures/validate", json=invalid_no_output)
    assert inv_res.status_code == 200
    assert inv_res.json()["valid"] is False
    assert "missing required 'output'" in inv_res.json()["error"].lower()

    # Unsupported check type
    invalid_bad_check = {
        "fixture": {
            "output": {},
            "checks": [{"type": "invalid_check_type"}],
        }
    }
    bad_res = client.post("/api/v1/fixtures/validate", json=invalid_bad_check)
    assert bad_res.status_code == 200
    assert bad_res.json()["valid"] is False
    assert "check validation error" in bad_res.json()["error"].lower()

