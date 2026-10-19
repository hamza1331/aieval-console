"""Cross-repository end-to-end fixture interoperability test.

Exports an evaluation run from Aieval Console and verifies that the aieval-py
CLI / execution engine runs the golden fixture cleanly conforming to FIXTURE_SPEC.md.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from aieval.cli.main import run_fixture
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db import seed as seed_module
from app.repositories.contract_repo import ContractRepository
from app.repositories.run_repo import RunRepository


def test_cross_repo_fixture_interoperability(
    client: TestClient,
    db_session: Session,
    test_engine,
    monkeypatch,
) -> None:
    """Verify that a fixture exported from Aieval Console executes cleanly in aieval-py."""
    # 1. Seed demo contract and runs
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr(seed_module, "SessionLocal", test_session_local)
    seed_module.seed_database(force=False)
    contracts = ContractRepository(db_session).list_contracts(limit=100)
    contract = next(contract for contract in contracts if contract.name == "Support ticket classification")
    runs = RunRepository(db_session).list_runs(contract_id=contract.id, limit=10)
    assert len(runs) > 0, "Expected at least one seeded evaluation run"
    run_id = runs[0].id

    # 2. Export fixture JSON via console API
    response = client.get(f"/api/v1/runs/{run_id}/fixture")
    assert response.status_code == 200
    fixture_dict = response.json()

    # Verify basic FIXTURE_SPEC.md structure
    assert "name" in fixture_dict
    assert "output" in fixture_dict
    assert "checks" in fixture_dict
    assert "expected" in fixture_dict

    # 3. Write exported fixture to disk and execute directly using aieval-py's runner
    with TemporaryDirectory() as tmp_dir:
        fixture_path = Path(tmp_dir) / "exported_golden_fixture.json"
        fixture_path.write_text(json.dumps(fixture_dict, indent=2))

        # Execute using aieval-py CLI runner
        exit_code = run_fixture(fixture_path)

        assert exit_code == 0
