"""Evaluations route (FR-04, FR-05, FR-06, FR-07, Phase 5 Batch)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evaluation import (
    BatchEvaluationRequest,
    BatchEvaluationResponse,
    EvaluationRequest,
    EvaluationResponse,
)
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post(
    "",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate output payload against a contract",
)
def evaluate_output(
    request: EvaluationRequest,
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    """Evaluates an AI output payload against a contract version or inline definition (FR-04, FR-07)."""
    service = EvaluationService(db)
    try:
        return service.evaluate_and_persist(
            output=request.output,
            contract_version_id=request.contract_version_id,
            contract_id=request.contract_id,
            inline_contract=request.contract,
            input_data=request.input,
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            ) from err
        if "must specify" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            ) from err
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err_msg,
        ) from err


@router.post(
    "/batch",
    response_model=BatchEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a batch of output payloads (up to 50 items)",
)
def evaluate_batch_outputs(
    request: BatchEvaluationRequest,
    db: Session = Depends(get_db),
) -> BatchEvaluationResponse:
    """Evaluates multiple output items against a contract in a single request (Phase 5)."""
    service = EvaluationService(db)
    try:
        return service.evaluate_batch(
            items=request.items,
            contract_version_id=request.contract_version_id,
            contract_id=request.contract_id,
            inline_contract=request.contract,
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            ) from err
        if "must specify" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            ) from err
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err_msg,
        ) from err
