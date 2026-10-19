"""Fixture export, validation, import, and replay service (FR-10, FR-16)."""

import re
import uuid
from typing import Any

import aieval
from sqlalchemy.orm import Session

from app.adapters.aieval_adapter import AievalAdapter
from app.repositories.contract_repo import ContractRepository
from app.repositories.review_repo import ReviewRepository
from app.repositories.run_repo import RunRepository
from app.schemas.contract import ContractSummaryResponse
from app.schemas.fixture import FixtureReplayResponse
from app.services.contract_service import ContractService


class FixtureService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.run_repo = RunRepository(db)
        self.contract_repo = ContractRepository(db)
        self.review_repo = ReviewRepository(db)

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
        if "checks" not in fixture:
            return False, "Fixture is missing required 'checks' attribute.", 0

        checks = fixture.get("checks")
        if not isinstance(checks, list) or len(checks) == 0:
            return False, "Fixture 'checks' must be a non-empty array of check specifications.", 0

        # Validate each check through core aieval-py factory
        try:
            for c in checks:
                if not isinstance(c, dict):
                    return False, f"Invalid check entry in checks array: {c}", 0
                aieval.build_check_from_spec(c)
        except (TypeError, ValueError, re.error) as err:
            return False, f"Check validation error: {err}", 0

        # Optional expected validation
        if "expected" in fixture:
            expected = fixture["expected"]
            if not isinstance(expected, dict):
                return False, "Attribute 'expected' must be an object if present.", 0
            if "passed" not in expected or not isinstance(expected["passed"], bool):
                return False, "Attribute 'expected.passed' must be a boolean.", 0
            if "failures" in expected:
                expected_failures = expected["failures"]
                if not isinstance(expected_failures, list):
                    return False, "Attribute 'expected.failures' must be an array.", 0
                for index, failure in enumerate(expected_failures):
                    if not isinstance(failure, dict):
                        return (
                            False,
                            f"Attribute 'expected.failures[{index}]' must be an object.",
                            0,
                        )
                    if not isinstance(failure.get("code"), str):
                        return (
                            False,
                            f"Attribute 'expected.failures[{index}].code' must be a string.",
                            0,
                        )
                    path = failure.get("path")
                    if path is not None and not isinstance(path, str):
                        return (
                            False,
                            f"Attribute 'expected.failures[{index}].path' must be a string or null.",
                            0,
                        )
                    severity = failure.get("severity", "error")
                    if severity not in ("info", "warning", "error", "critical"):
                        return (
                            False,
                            f"Attribute 'expected.failures[{index}].severity' is invalid.",
                            0,
                        )

        return True, None, len(checks)

    def replay_fixture(
        self,
        fixture: dict[str, Any],
        persist_run: bool = True,
        contract_id: str | None = None,
    ) -> FixtureReplayResponse:
        """Executes a fixture through aieval-py and computes regression/parity diagnostics."""
        is_valid, err_msg, _ = self.validate_fixture(fixture)
        if not is_valid:
            raise ValueError(f"Invalid fixture payload: {err_msg}")

        output = fixture.get("output")
        checks = fixture.get("checks", [])
        context = fixture.get("context", {})
        input_data = context.get("input") if isinstance(context, dict) else None

        # Execute evaluation via adapter
        eval_res = AievalAdapter.evaluate(
            output=output,
            checks_spec=checks,
            context_data=context,
            run_id=str(uuid.uuid4()),
        )

        expected_block = fixture.get("expected", {})
        expected_passed = expected_block.get("passed", True)
        actual_passed = eval_res.status == "passed"
        expected_status = "passed" if expected_passed else "failed"

        differences: list[str] = []
        parity_status = "match"

        if actual_passed and not expected_passed:
            parity_status = "divergence"
            differences.append("Fixture expected failure, but actual evaluation passed.")
        elif not actual_passed and expected_passed:
            parity_status = "regression"
            differences.append(
                f"REGRESSION: Fixture expected clean pass, but actual evaluation failed with {len(eval_res.failures)} error(s)."
            )
        elif not actual_passed and not expected_passed and "failures" in expected_block:
            unmatched_actual = [
                {"code": failure.code, "path": failure.path, "severity": failure.severity}
                for failure in eval_res.failures
            ]
            expected_failures = expected_block["failures"]
            matched_expected: dict[int, int] = {}

            def match_expected(expected_index: int, seen_actual: set[int]) -> bool:
                expected_failure = expected_failures[expected_index]
                for actual_index, actual_failure in enumerate(unmatched_actual):
                    if actual_index in seen_actual or not all(
                        key not in expected_failure
                        or expected_failure[key] == actual_failure[key]
                        for key in ("code", "path", "severity")
                    ):
                        continue
                    seen_actual.add(actual_index)
                    if actual_index not in matched_expected or match_expected(
                        matched_expected[actual_index], seen_actual
                    ):
                        matched_expected[actual_index] = expected_index
                        return True
                return False

            missing_expected = [
                expected_failure
                for index, expected_failure in enumerate(expected_failures)
                if not match_expected(index, set())
            ]
            extra_actual = [
                failure
                for index, failure in enumerate(unmatched_actual)
                if index not in matched_expected
            ]

            if missing_expected or extra_actual:
                parity_status = "divergence"
                if missing_expected:
                    differences.append(f"Missing expected failures: {missing_expected}")
                if extra_actual:
                    differences.append(f"Unexpected additional failures: {extra_actual}")

        run_id = None
        if persist_run and contract_id:
            contract = self.contract_repo.get_by_id(contract_id)
            version = self.contract_repo.get_latest_version(contract_id)
            if contract is None or version is None:
                raise ValueError(f"Contract '{contract_id}' not found or has no version.")
            if contract.status == "archived":
                raise ValueError(f"Cannot persist replay to archived contract '{contract_id}'.")
            if version.definition_json.get("checks") != checks:
                raise ValueError(
                    "Cannot persist fixture replay: fixture checks do not match the selected "
                    "contract's latest version."
                )

            run = self.run_repo.create_run(
                contract_version_id=version.id,
                status=eval_res.status,
                input_json=input_data,
                output_json=output,
                result_json=eval_res.model_dump(),
                duration_ms=eval_res.duration_ms,
                aieval_version=aieval.__version__,
            )
            run_id = run.id
            self.review_repo.create_review(run_id=run_id)
            self.db.commit()
            eval_res.run_id = run_id

        return FixtureReplayResponse(
            run_id=run_id,
            actual_status=eval_res.status,
            expected_status=expected_status,
            parity_status=parity_status,
            matches_expected=(parity_status == "match"),
            failures_count=len(eval_res.failures),
            duration_ms=eval_res.duration_ms,
            differences=differences,
            failures=[f.model_dump() for f in eval_res.failures],
        )

    def import_fixture_as_contract(
        self,
        fixture: dict[str, Any],
        contract_name: str | None = None,
    ) -> ContractSummaryResponse:
        """Imports fixture checks as a new declarative validation contract."""
        is_valid, err_msg, _ = self.validate_fixture(fixture)
        if not is_valid:
            raise ValueError(f"Invalid fixture payload: {err_msg}")

        name = contract_name or fixture.get("name") or "Imported Contract"
        description = fixture.get("description") or "Imported from golden test fixture"
        checks = fixture.get("checks", [])

        contract_service = ContractService(self.db)
        detail = contract_service.create_contract(
            name=name,
            description=description,
            checks=checks,
        )
        return ContractSummaryResponse(
            id=detail.id,
            name=detail.name,
            description=detail.description,
            status=detail.status,
            latest_version=detail.versions[0].version if detail.versions else 1,
            total_versions=len(detail.versions),
            created_at=detail.created_at,
            updated_at=detail.updated_at,
        )
