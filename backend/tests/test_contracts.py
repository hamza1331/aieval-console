"""Tests for contracts API and versioning (FR-01, FR-02, FR-03)."""

from fastapi.testclient import TestClient

SAMPLE_CHECKS = [
    {
        "type": "required_fields",
        "fields": ["category", "priority"],
    },
    {
        "type": "enum",
        "field": "category",
        "allowed": ["billing", "technical"],
    },
]


def test_create_contract_and_initial_version(client: TestClient) -> None:
    payload = {
        "name": "Support Classifier",
        "description": "Validates ticket categorization",
        "checks": SAMPLE_CHECKS,
    }
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Support Classifier"
    assert data["description"] == "Validates ticket categorization"
    assert data["status"] == "active"
    assert len(data["versions"]) == 1
    assert data["versions"][0]["version"] == 1
    assert data["versions"][0]["definition_json"]["checks"] == SAMPLE_CHECKS
    assert "definition_hash" in data["versions"][0]


def test_create_contract_invalid_checks_returns_422(client: TestClient) -> None:
    payload = {
        "name": "Invalid Contract",
        "checks": [{"type": "unsupported_check_type"}],
    }
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422
    assert "unsupported check type" in response.json()["detail"].lower()


def test_list_contracts_and_pagination(client: TestClient) -> None:
    # Create two contracts
    client.post(
        "/api/v1/contracts",
        json={"name": "Contract A", "checks": SAMPLE_CHECKS},
    )
    client.post(
        "/api/v1/contracts",
        json={"name": "Contract B", "checks": SAMPLE_CHECKS},
    )

    response = client.get("/api/v1/contracts?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    assert data["limit"] == 10
    assert data["offset"] == 0


def test_get_contract_detail_and_not_found(client: TestClient) -> None:
    create_res = client.post(
        "/api/v1/contracts",
        json={"name": "Detail Test", "checks": SAMPLE_CHECKS},
    )
    contract_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/contracts/{contract_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == contract_id

    missing_res = client.get("/api/v1/contracts/non-existent-uuid")
    assert missing_res.status_code == 404


def test_update_contract_metadata_and_archive(client: TestClient) -> None:
    create_res = client.post(
        "/api/v1/contracts",
        json={"name": "To Archive", "checks": SAMPLE_CHECKS},
    )
    contract_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"name": "Archived Contract", "status": "archived"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Archived Contract"
    assert patch_res.json()["status"] == "archived"

    # Verify listing with status filter
    archived_list = client.get("/api/v1/contracts?status=archived")
    assert archived_list.status_code == 200
    names = [c["name"] for c in archived_list.json()["items"]]
    assert "Archived Contract" in names


def test_create_sequential_immutable_versions(client: TestClient) -> None:
    create_res = client.post(
        "/api/v1/contracts",
        json={"name": "Versioning Test", "checks": SAMPLE_CHECKS},
    )
    contract_id = create_res.json()["id"]

    # Add Version 2
    new_checks_v2 = [
        {"type": "required_fields", "fields": ["category", "priority", "notes"]},
    ]
    v2_res = client.post(
        f"/api/v1/contracts/{contract_id}/versions",
        json={"checks": new_checks_v2},
    )
    assert v2_res.status_code == 201
    assert v2_res.json()["version"] == 2

    # Add Version 3
    new_checks_v3 = [
        {"type": "required_fields", "fields": ["category", "priority", "notes", "tags"]},
    ]
    v3_res = client.post(
        f"/api/v1/contracts/{contract_id}/versions",
        json={"checks": new_checks_v3},
    )
    assert v3_res.status_code == 201
    assert v3_res.json()["version"] == 3

    # Verify specific versions are retrievable
    get_v1 = client.get(f"/api/v1/contracts/{contract_id}/versions/1")
    assert get_v1.status_code == 200
    assert get_v1.json()["version"] == 1

    get_v2 = client.get(f"/api/v1/contracts/{contract_id}/versions/2")
    assert get_v2.status_code == 200
    assert get_v2.json()["version"] == 2

    # Check contract detail includes all 3 versions ordered descending
    detail = client.get(f"/api/v1/contracts/{contract_id}").json()
    assert len(detail["versions"]) == 3
    assert [v["version"] for v in detail["versions"]] == [3, 2, 1]


def test_cannot_create_version_for_archived_contract(client: TestClient) -> None:
    create_res = client.post(
        "/api/v1/contracts",
        json={"name": "Archive Lock Test", "checks": SAMPLE_CHECKS},
    )
    contract_id = create_res.json()["id"]

    client.patch(f"/api/v1/contracts/{contract_id}", json={"status": "archived"})

    v2_res = client.post(
        f"/api/v1/contracts/{contract_id}/versions",
        json={"checks": SAMPLE_CHECKS},
    )
    assert v2_res.status_code == 422
    assert "archived" in v2_res.json()["detail"].lower()


def test_cannot_evaluate_archived_contract_by_id(client: TestClient) -> None:
    create_res = client.post(
        "/api/v1/contracts",
        json={"name": "Archived Evaluation Test", "checks": SAMPLE_CHECKS},
    )
    contract_id = create_res.json()["id"]
    client.patch(f"/api/v1/contracts/{contract_id}", json={"status": "archived"})

    response = client.post(
        "/api/v1/evaluations",
        json={"contract_id": contract_id, "output": {"category": "billing", "priority": "low"}},
    )

    assert response.status_code == 422
    assert "archived" in response.json()["detail"].lower()
