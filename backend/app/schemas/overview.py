"""Dashboard overview schemas (FR-11)."""

from pydantic import BaseModel, Field

from app.schemas.run import RunSummaryResponse


class OverviewResponse(BaseModel):
    """Aggregate statistics and recent activity for the dashboard overview."""

    total_contracts: int = Field(..., description="Total contracts count")
    active_contracts: int = Field(..., description="Count of active contracts")
    total_runs: int = Field(..., description="Total evaluation runs")
    passed_runs: int = Field(..., description="Count of passed runs")
    failed_runs: int = Field(..., description="Count of failed runs")
    pass_rate: float = Field(..., description="Pass percentage (0.0 to 100.0)")
    unreviewed_failures: int = Field(..., description="Failed runs awaiting human review")
    recent_runs: list[RunSummaryResponse] = Field(
        default_factory=list,
        description="List of up to 10 most recent evaluation runs",
    )
