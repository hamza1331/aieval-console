"""Cross-repository end-to-end fixture interoperability test.

Exports an evaluation run from Aieval Console and verifies that the aieval-py
CLI / execution engine runs the golden fixture cleanly conforming to FIXTURE_SPEC.md.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from aieval.cli.main import run_fixture
from fastapi.testclient import TestClient

from app.db.seed import seed_database
from app.db.session import SessionLocal
from app.main import create_app
from app.repositories.run_repo import RunRepository


def test_cross_repo_fixture_interoperability():
    """Verify that a fixture exported from Aieval Console executes cleanly in aieval-py."""
    # 1. Seed demo contract and runs
    seed_database(force=False)
    db = SessionLocal()
    try:
        repo = RunRepository(db)
        runs = repo.list_runs(limit=10)
        assert len(runs) > 0, "Expected at least one seeded evaluation run"
        run_id = runs[0].id
    finally:
        db.close()

    # 2. Export fixture JSON via console API
    app = create_app()
    client = TestClient(app)
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

        expected_passed = fixture_dict["expected"]["passed"]
        expected_exit_code = 0 if expected_passed else 1
        assert exit_code == expected_exit_code
