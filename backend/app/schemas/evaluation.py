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
    contract_id: str | None = Field(
        default=None,
        description="ID of the contract (will evaluate against its latest active version).",
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


class BatchEvaluationItem(BaseModel):
    """Individual item within a batch evaluation request."""

    item_id: str | None = Field(default=None, description="Optional client-defined item identifier")
    input: dict[str, Any] | None = Field(default=None, description="Optional input/prompt context")
    output: Any = Field(..., description="AI output data to evaluate")


class BatchEvaluationRequest(BaseModel):
    """Batch submission for evaluating multiple outputs against a contract."""

    contract_version_id: str | None = Field(
        default=None, description="ID of specific contract version"
    )
    contract_id: str | None = Field(
        default=None, description="ID of contract (uses latest active version)"
    )
    contract: ContractDefinitionSchema | None = Field(
        default=None, description="Optional inline contract definition"
    )
    items: list[BatchEvaluationItem] = Field(
        ..., min_length=1, max_length=50, description="List of items to evaluate (max 50)"
    )


class BatchItemOutcome(BaseModel):
    """Individual evaluation outcome in a batch."""

    item_id: str | None = None
    run_id: str
    status: str
    failures: list[FailureSchema] = Field(default_factory=list)
    warnings: list[FailureSchema] = Field(default_factory=list)
    duration_ms: float


class BatchEvaluationResponse(BaseModel):
    """Aggregate outcome of batch evaluation."""

    total_items: int
    passed_count: int
    failed_count: int
    pass_rate: float
    total_duration_ms: float
    results: list[BatchItemOutcome]
