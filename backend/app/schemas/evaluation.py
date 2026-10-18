"""Evaluation request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.contract import ContractDefinitionSchema


class EvaluationRequest(BaseModel):
    """Payload submission for evaluation."""

    contract_version_id: str | None = Field(
        default=None,
        description="ID of the stored contract version to evaluate against.",
    )
    contract: ContractDefinitionSchema | None = Field(
        default=None,
        description="Inline declarative contract definition (used for prototyping / workbench).",
    )
    input: dict[str, Any] | None = Field(
        default=None,
        description="Optional input / prompt context that generated the output.",
    )
    output: Any = Field(
        ...,
        description="AI output data to evaluate (dict, string, list, or primitive).",
    )


class FailureSchema(BaseModel):
    """Normalized evaluation failure issue."""

    code: str = Field(..., description="Standardized failure code")
    message: str = Field(..., description="Human-readable explanation of failure")
    severity: str = Field(default="error", description="Failure severity level")
    path: str | None = Field(default=None, description="Path to invalid field if applicable")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Diagnostic failure metadata"
    )
    suggested_repair: str | None = Field(default=None, description="Optional suggested fix")


class EvaluationSummarySchema(BaseModel):
    """Statistical summary of an evaluation run."""

    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings_count: int
    duration_ms: float


class EvaluationResponse(BaseModel):
    """Standard normalized evaluation outcome."""

    run_id: str = Field(..., description="Unique run identifier")
    status: str = Field(..., description="'passed' or 'failed'")
    contract_version: int | None = Field(default=None, description="Contract version number")
    duration_ms: float = Field(..., description="Execution duration in milliseconds")
    summary: EvaluationSummarySchema = Field(..., description="Check execution counts and duration")
    failures: list[FailureSchema] = Field(
        default_factory=list, description="List of blocking failures"
    )
    warnings: list[FailureSchema] = Field(
        default_factory=list, description="List of non-blocking warnings"
    )
