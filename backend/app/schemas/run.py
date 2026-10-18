"""Evaluation run response and inspection schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.review import ReviewResponse


class RunSummaryResponse(BaseModel):
    """Summary of an evaluation run for paginated lists."""

    id: str
    contract_id: str
    contract_name: str
    contract_version_id: str
    contract_version_number: int
    status: str
    failed_checks: int
    total_checks: int
    duration_ms: float
    review_status: str
    created_at: datetime


class RunDetailResponse(BaseModel):
    """Complete detail of a single evaluation run."""

    id: str
    contract_id: str
    contract_name: str
    contract_version_id: str
    contract_version_number: int
    status: str
    input_json: dict[str, Any] | None = None
    output_json: Any
    result_json: dict[str, Any]
    duration_ms: float
    aieval_version: str
    created_at: datetime
    review: ReviewResponse | None = None
