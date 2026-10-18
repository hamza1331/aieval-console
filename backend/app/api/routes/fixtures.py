"""Golden fixture export and validation routes (FR-10, FR-16)."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fixture import FixtureValidateRequest, FixtureValidateResponse
from app.services.fixture_service import FixtureService

router = APIRouter(tags=["fixtures"])


@router.get(
    "/runs/{id}/fixture",
    summary="Export an evaluation run as a golden regression fixture (FR-10)",
)
def export_run_fixture(
    id: str,
    download: bool = False,
    db: Session = Depends(get_db),
) -> Any:
    service = FixtureService(db)
    try:
        fixture_data = service.export_fixture(id)
        if download:
            import json

            content = json.dumps(fixture_data, indent=2)
            short_id = id[:8]
            headers = {
                "Content-Disposition": f'attachment; filename="golden_fixture_{short_id}.json"'
            }
            return Response(content=content, media_type="application/json", headers=headers)
        return fixture_data
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.post(
    "/fixtures/validate",
    response_model=FixtureValidateResponse,
    summary="Validate external fixture format without executing code (FR-16)",
)
def validate_fixture(
    payload: FixtureValidateRequest,
    db: Session = Depends(get_db),
) -> FixtureValidateResponse:
    service = FixtureService(db)
    is_valid, error_msg, checks_count = service.validate_fixture(payload.fixture)
    return FixtureValidateResponse(
        valid=is_valid,
        error=error_msg,
        checks_count=checks_count,
    )

