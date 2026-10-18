"""Fixture export and validation service (FR-10, FR-16)."""

from typing import Any

import aieval
from sqlalchemy.orm import Session

from app.repositories.run_repo import RunRepository


class FixtureService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.run_repo = RunRepository(db)

    def export_fixture(self, run_id: str) -> dict[str, Any]:
        """Exports a run as a portable golden fixture adhering to FIXTURE_SPEC.md."""
        run = self.run_repo.get_by_id(run_id)
        if not run:
            raise ValueError(f"Evaluation run '{run_id}' not found.")

        contract_version = run.contract_version
        contract = contract_version.contract if contract_version else None
        contract_name = contract.name if contract else "Unknown Contract"
        version_num = contract_version.version if contract_version else 1
        checks = (
            contract_version.definition_json.get("checks", []) if contract_version else []
        )

        failures_list = [
            {
                "code": f["code"],
                "path": f.get("path"),
                "severity": f.get("severity", "error"),
            }
            for f in run.result_json.get("failures", [])
        ]

        short_id = run.id[:8]
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "name": f"golden_fixture_{short_id}",
            "description": f"Regression fixture exported from run {short_id} ({contract_name} v{version_num})",
            "context": {
                "input": run.input_json,
                "metadata": {
                    "contract_name": contract_name,
                    "contract_version": version_num,
                    "console_run_id": run.id,
                },
            },
            "output": run.output_json,
            "checks": checks,
            "expected": {
                "passed": run.status == "passed",
                "failures": failures_list,
            },
        }

    def validate_fixture(self, fixture: dict[str, Any]) -> tuple[bool, str | None, int]:
        """Validates fixture schema and check definitions without arbitrary code execution."""
        if not isinstance(fixture, dict):
            return False, "Fixture must be a JSON object dictionary.", 0

        if "output" not in fixture:
            return False, "Fixture is missing required 'output' attribute.", 0

        checks = fixture.get("checks")
        if not isinstance(checks, list) or len(checks) == 0:
            return False, "Fixture 'checks' must be a non-empty array of check specifications.", 0

        # Validate each check through core aieval-py factory
        try:
            for c in checks:
                if not isinstance(c, dict):
                    return False, f"Invalid check entry in checks array: {c}", 0
                aieval.build_check_from_spec(c)
        except Exception as err:
            return False, f"Check validation error: {err}", 0

        # Optional expected validation
        if "expected" in fixture:
            expected = fixture["expected"]
            if not isinstance(expected, dict):
                return False, "Attribute 'expected' must be an object if present.", 0
            if "passed" not in expected or not isinstance(expected["passed"], bool):
                return False, "Attribute 'expected.passed' must be a boolean.", 0

        return True, None, len(checks)
