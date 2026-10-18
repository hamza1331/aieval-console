"""Tests for run history listing, filtering, and inspection (FR-08, FR-12)."""

from fastapi.testclient import TestClient

CHECKS = [{"type": "required_fields", "fields": ["status_code"]}]


def test_runs_listing_and_filtering(client: TestClient) -> None:
    # 1. Create contract
    contract_res = client.post(
        "/api/v1/contracts",
        json={"name": "Run Filtering Contract", "checks": CHECKS},
    )
    contract_id = contract_res.json()["id"]
    version_id = contract_res.json()["versions"][0]["id"]

    # 2. Submit 1 passing run and 1 failing run
    client.post(
        "/api/v1/evaluations",
        json={
            "contract_version_id": version_id,
            "output": {"status_code": 200},
        },
    )
    client.post(
        "/api/v1/evaluations",
        json={
            "contract_version_id": version_id,
            "output": {"wrong_field": 1},
        },
    )

    # 3. List all runs for this contract
    runs_res = client.get(f"/api/v1/runs?contract_id={contract_id}")
    assert runs_res.status_code == 200
    data = runs_res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 4. Filter by status="passed"
    passed_res = client.get(f"/api/v1/runs?contract_id={contract_id}&status=passed")
    assert passed_res.status_code == 200
    assert passed_res.json()["total"] == 1
    assert passed_res.json()["items"][0]["status"] == "passed"

    # 5. Filter by status="failed"
    failed_res = client.get(f"/api/v1/runs?contract_id={contract_id}&status=failed")
    assert failed_res.status_code == 200
    assert failed_res.json()["total"] == 1
    assert failed_res.json()["items"][0]["status"] == "failed"

    # 6. Filter by date range
    future_date = "2099-01-01T00:00:00Z"
    future_res = client.get(f"/api/v1/runs?contract_id={contract_id}&from_date={future_date}")
    assert future_res.status_code == 200
    assert future_res.json()["total"] == 0

    past_date = "2000-01-01T00:00:00Z"
    past_res = client.get(f"/api/v1/runs?contract_id={contract_id}&from_date={past_date}")
    assert past_res.status_code == 200
    assert past_res.json()["total"] == 2


def test_get_run_detail_and_not_found(client: TestClient) -> None:
    # 1. Create contract & evaluate
    contract_res = client.post(
        "/api/v1/contracts",
        json={"name": "Detail Inspector Contract", "checks": CHECKS},
    )
    version_id = contract_res.json()["versions"][0]["id"]

    eval_res = client.post(
        "/api/v1/evaluations",
        json={
            "contract_version_id": version_id,
            "input": {"prompt": "generate status"},
            "output": {"status_code": 200},
        },
    )
    run_id = eval_res.json()["run_id"]

    # 2. Get detail
    detail_res = client.get(f"/api/v1/runs/{run_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == run_id
    assert detail["contract_name"] == "Detail Inspector Contract"
    assert detail["status"] == "passed"
    assert detail["input_json"]["prompt"] == "generate status"
    assert "review" in detail
    assert detail["review"]["status"] == "unreviewed"

    # 3. Not found
    missing_res = client.get("/api/v1/runs/non-existent-uuid")
    assert missing_res.status_code == 404
