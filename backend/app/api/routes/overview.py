"""Dashboard overview routes (FR-11)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.overview import OverviewResponse
from app.services.overview_service import OverviewService

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get(
    "",
    response_model=OverviewResponse,
    summary="Get dashboard overview totals, metrics, and recent activity",
)
def get_dashboard_overview(
    db: Session = Depends(get_db),
) -> OverviewResponse:
    service = OverviewService(db)
    return service.get_overview()

