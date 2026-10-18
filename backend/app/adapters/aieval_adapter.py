"""Adapter integrating aieval-py validation engine with the console application."""

import uuid
from typing import Any

import aieval
from aieval.domain import EvaluationContext, EvaluationResult

from app.schemas.evaluation import (
    EvaluationResponse,
    EvaluationSummarySchema,
    FailureSchema,
)


class AievalAdapter:
    """Translates contract check specs to aieval-py checks and normalizes execution results."""

    @staticmethod
    def evaluate(
        output: Any,
        checks_spec: list[dict[str, Any]],
        context_data: dict[str, Any] | None = None,
        run_id: str | None = None,
        contract_version: int | None = None,
    ) -> EvaluationResponse:
        """Executes aieval-py checks against output and returns normalized response."""
        effective_run_id = run_id or str(uuid.uuid4())

        # 1. Translate declarative specs to aieval-py checks
        checks = [aieval.build_check_from_spec(spec) for spec in checks_spec]

        # 2. Build EvaluationContext
        context: EvaluationContext | None = None
        if context_data:
            context = EvaluationContext(
                input=context_data.get("input"),
                prompt=context_data.get("prompt"),
                model=context_data.get("model"),
                metadata=context_data.get("metadata", {}),
            )

        # 3. Execute evaluation via core engine
        result: EvaluationResult = aieval.evaluate(output, checks=checks, context=context)

        # 4. Map failures & warnings
        failures = [
            FailureSchema(
                code=f.code.value if hasattr(f.code, "value") else str(f.code),
                message=f.message,
                severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                path=str(f.path) if f.path is not None else None,
                metadata=dict(f.metadata),
                suggested_repair=f.suggested_repair,
            )
            for f in result.failures
        ]

        warnings = [
            FailureSchema(
                code=w.code.value if hasattr(w.code, "value") else str(w.code),
                message=w.message,
                severity=w.severity.value if hasattr(w.severity, "value") else str(w.severity),
                path=str(w.path) if w.path is not None else None,
                metadata=dict(w.metadata),
            )
            for w in result.warnings
        ]

        # 5. Build normalized response
        return EvaluationResponse(
            run_id=effective_run_id,
            status="passed" if result.passed else "failed",
            contract_version=contract_version,
            duration_ms=round(result.summary.duration_ms, 3),
            summary=EvaluationSummarySchema(
                total_checks=result.summary.total_checks,
                passed_checks=result.summary.passed_checks,
                failed_checks=result.summary.failed_checks,
                warnings_count=result.summary.warnings_count,
                duration_ms=round(result.summary.duration_ms, 3),
            ),
            failures=failures,
            warnings=warnings,
        )
