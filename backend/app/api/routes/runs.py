"""Runs history, filtering, export, and inspection routes (FR-08, FR-12, Phase 5)."""

import csv
import io
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.run import RunDetailResponse, RunSummaryResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get(
    "",
    response_model=PaginatedResponse[RunSummaryResponse],
    summary="List evaluation runs with filters and pagination",
)
def list_runs(
    contract_id: str | None = Query(None, description="Filter by contract ID"),
    status: str | None = Query(None, description="Filter by run status: 'passed' or 'failed'"),
    review_status: str | None = Query(
        None, description="Filter by review status: 'unreviewed' or 'reviewed'"
    ),
    from_date: datetime | None = Query(None, description="Filter runs after ISO timestamp"),
    to_date: datetime | None = Query(None, description="Filter runs before ISO timestamp"),
    min_duration_ms: float | None = Query(None, ge=0.0, description="Minimum duration in ms"),
    max_duration_ms: float | None = Query(None, ge=0.0, description="Maximum duration in ms"),
    failure_code: str | None = Query(None, description="Filter by failure code, e.g. ENUM_MISMATCH"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedResponse[RunSummaryResponse]:
    service = EvaluationService(db)
    items, total = service.list_runs(
        contract_id=contract_id,
        status=status,
        review_status=review_status,
        from_date=from_date,
        to_date=to_date,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        failure_code=failure_code,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/export",
    summary="Export filtered runs summary as CSV or JSON report (Phase 5)",
)
def export_runs(
    export_format: str = Query("csv", alias="format", description="Export format: 'csv' or 'json'"),
    contract_id: str | None = Query(None, description="Filter by contract ID"),
    status: str | None = Query(None, description="Filter by run status: 'passed' or 'failed'"),
    review_status: str | None = Query(None, description="Filter by review status"),
    from_date: datetime | None = Query(None, description="Filter runs after ISO timestamp"),
    to_date: datetime | None = Query(None, description="Filter runs before ISO timestamp"),
    min_duration_ms: float | None = Query(None, ge=0.0),
    max_duration_ms: float | None = Query(None, ge=0.0),
    failure_code: str | None = Query(None, description="Filter by failure code"),
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> Any:
    service = EvaluationService(db)
    items, _ = service.list_runs(
        contract_id=contract_id,
        status=status,
        review_status=review_status,
        from_date=from_date,
        to_date=to_date,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        failure_code=failure_code,
        limit=limit,
        offset=0,
    )

    if export_format.lower() == "json":
        data = [i.model_dump(mode="json") for i in items]
        content = json.dumps(data, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="evaluation_runs_report.json"'},
        )

    # Default CSV export
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "run_id",
            "contract_id",
            "contract_name",
            "version",
            "status",
            "failed_checks",
            "total_checks",
            "duration_ms",
            "review_status",
            "created_at",
        ]
    )
    for i in items:
        writer.writerow(
            [
                i.id,
                i.contract_id,
                i.contract_name,
                i.contract_version_number,
                i.status,
                i.failed_checks,
                i.total_checks,
                f"{i.duration_ms:.2f}",
                i.review_status,
                i.created_at.isoformat(),
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="evaluation_runs_report.csv"'},
    )


@router.get(
    "/{id}",
    response_model=RunDetailResponse,
    summary="Get full run details, failure breakdown, and review note",
)
def get_run(
    id: str,
    db: Session = Depends(get_db),
) -> RunDetailResponse:
    service = EvaluationService(db)
    run = service.get_run(id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{id}' not found.",
        )
    return run
