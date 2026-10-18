"""Tests for run reviews and annotations (FR-09)."""

from fastapi.testclient import TestClient

CHECKS = [{"type": "required_fields", "fields": ["status"]}]


def test_update_run_review_and_status(client: TestClient) -> None:
    # 1. Create contract and evaluate run
    contract_res = client.post(
        "/api/v1/contracts",
        json={"name": "Review Test Contract", "checks": CHECKS},
    )
    version_id = contract_res.json()["versions"][0]["id"]

    eval_res = client.post(
        "/api/v1/evaluations",
        json={
            "contract_version_id": version_id,
            "output": {"status": "wrong"},
        },
    )
    run_id = eval_res.json()["run_id"]

    # 2. Add review note and set status="reviewed"
    patch_res = client.patch(
        f"/api/v1/runs/{run_id}/review",
        json={
            "status": "reviewed",
            "note": "Investigated by QA: LLM hallucinated invalid status string.",
        },
    )
    assert patch_res.status_code == 200
    review_data = patch_res.json()
    assert review_data["status"] == "reviewed"
    assert "Investigated by QA" in review_data["note"]

    # 3. Verify in run detail
    run_detail = client.get(f"/api/v1/runs/{run_id}").json()
    assert run_detail["review"]["status"] == "reviewed"
    assert "Investigated by QA" in run_detail["review"]["note"]


def test_review_invalid_status_returns_400(client: TestClient) -> None:
    contract_res = client.post(
        "/api/v1/contracts",
        json={"name": "Review Error Contract", "checks": CHECKS},
    )
    version_id = contract_res.json()["versions"][0]["id"]

    eval_res = client.post(
        "/api/v1/evaluations",
        json={"contract_version_id": version_id, "output": {"status": "ok"}},
    )
    run_id = eval_res.json()["run_id"]

    patch_res = client.patch(
        f"/api/v1/runs/{run_id}/review",
        json={"status": "invalid_status_value"},
    )
    assert patch_res.status_code == 400
    assert "must be 'unreviewed' or 'reviewed'" in patch_res.json()["detail"].lower()


def test_review_non_existent_run_returns_404(client: TestClient) -> None:
    patch_res = client.patch(
        "/api/v1/runs/non-existent-run-id/review",
        json={"status": "reviewed", "note": "test"},
    )
    assert patch_res.status_code == 404

