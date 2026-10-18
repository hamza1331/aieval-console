"""Runs history and inspection routes (FR-08, FR-12)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    from_date: datetime | None = Query(None, description="Filter runs after ISO timestamp"),
    to_date: datetime | None = Query(None, description="Filter runs before ISO timestamp"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedResponse[RunSummaryResponse]:
    service = EvaluationService(db)
    items, total = service.list_runs(
        contract_id=contract_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
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

