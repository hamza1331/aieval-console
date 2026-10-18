"""Review routes (FR-09)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review import ReviewResponse, ReviewUpdateRequest
from app.services.review_service import ReviewService

router = APIRouter(prefix="/runs", tags=["reviews"])


@router.patch(
    "/{id}/review",
    response_model=ReviewResponse,
    summary="Add/update review note and reviewed status for a run",
)
def update_run_review(
    id: str,
    payload: ReviewUpdateRequest,
    db: Session = Depends(get_db),
) -> ReviewResponse:
    service = ReviewService(db)
    try:
        return service.update_review(
            run_id=id,
            status=payload.status,
            note=payload.note,
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            ) from err
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        ) from err

