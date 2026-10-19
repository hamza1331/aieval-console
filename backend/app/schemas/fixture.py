"""Golden test fixture schemas (FR-10, FR-16)."""

from typing import Any

from pydantic import BaseModel, Field


class FixtureValidateRequest(BaseModel):
    """Payload to validate an existing or external fixture."""

    fixture: dict[str, Any] = Field(..., description="Fixture JSON object")


class FixtureValidateResponse(BaseModel):
    """Result of fixture validation."""

    valid: bool = Field(..., description="Whether the fixture conforms to the specification")
    error: str | None = Field(default=None, description="Validation failure explanation")
    checks_count: int = Field(default=0, description="Number of valid checks parsed")


class FixtureReplayRequest(BaseModel):
    """Payload to replay an imported fixture against the evaluation engine."""

    fixture: dict[str, Any] = Field(
        ..., description="Fixture JSON object conforming to FIXTURE_SPEC.md"
    )
    persist_run: bool = Field(default=True, description="Whether to store the replay run")
    contract_id: str | None = Field(
        default=None, description="Optional contract ID to bind the replay to"
    )


class FixtureReplayResponse(BaseModel):
    """Outcome of replaying a fixture, including parity analysis."""

    run_id: str | None = Field(default=None, description="Persisted evaluation run ID if stored")
    actual_status: str = Field(..., description="'passed' or 'failed'")
    expected_status: str = Field(
        ..., description="'passed' or 'failed' from fixture expected block"
    )
    parity_status: str = Field(
        ..., description="'match' | 'regression' | 'divergence'"
    )
    matches_expected: bool = Field(
        ..., description="True if actual outcome matches expected behavior"
    )
    failures_count: int
    duration_ms: float
    differences: list[str] = Field(
        default_factory=list, description="Diagnostic descriptions of discrepancies"
    )
    failures: list[dict[str, Any]] = Field(default_factory=list)


class FixtureImportRequest(BaseModel):
    """Payload to import a fixture and create a declarative contract."""

    fixture: dict[str, Any] = Field(..., description="Fixture JSON object")
    contract_name: str | None = Field(default=None, description="Optional override contract name")
