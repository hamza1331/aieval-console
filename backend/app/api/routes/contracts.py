"""Contracts management routes (FR-01, FR-02, FR-03)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.contract import (
    ContractCreateRequest,
    ContractDetailResponse,
    ContractDiffResponse,
    ContractSummaryResponse,
    ContractUpdateRequest,
    ContractVersionCreateRequest,
    ContractVersionResponse,
)
from app.services.contract_service import ContractService

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post(
    "",
    response_model=ContractDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create contract and initial version 1",
)
def create_contract(
    payload: ContractCreateRequest,
    db: Session = Depends(get_db),
) -> ContractDetailResponse:
    service = ContractService(db)
    try:
        return service.create_contract(
            name=payload.name,
            description=payload.description,
            checks=payload.checks,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err


@router.get(
    "",
    response_model=PaginatedResponse[ContractSummaryResponse],
    summary="List contracts with pagination and status filter",
)
def list_contracts(
    status: str | None = Query(None, description="Filter by status: 'active' or 'archived'"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ContractSummaryResponse]:
    service = ContractService(db)
    items, total = service.list_contracts(status=status, limit=limit, offset=offset)
    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{id}",
    response_model=ContractDetailResponse,
    summary="Get contract detail and version history",
)
def get_contract(
    id: str,
    db: Session = Depends(get_db),
) -> ContractDetailResponse:
    service = ContractService(db)
    contract = service.get_contract(id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract '{id}' not found.",
        )
    return contract


@router.patch(
    "/{id}",
    response_model=ContractDetailResponse,
    summary="Update contract metadata or archive",
)
def update_contract(
    id: str,
    payload: ContractUpdateRequest,
    db: Session = Depends(get_db),
) -> ContractDetailResponse:
    service = ContractService(db)
    try:
        updated = service.update_contract(
            contract_id=id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract '{id}' not found.",
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.post(
    "/{id}/versions",
    response_model=ContractVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sequential immutable version",
)
def create_contract_version(
    id: str,
    payload: ContractVersionCreateRequest,
    db: Session = Depends(get_db),
) -> ContractVersionResponse:
    service = ContractService(db)
    try:
        return service.create_new_version(
            contract_id=id,
            checks=payload.checks,
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            ) from err
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err_msg,
        ) from err


@router.get(
    "/{id}/versions/{version}",
    response_model=ContractVersionResponse,
    summary="Get specific contract version definition",
)
def get_contract_version(
    id: str,
    version: int,
    db: Session = Depends(get_db),
) -> ContractVersionResponse:
    service = ContractService(db)
    version_obj = service.get_version(id, version)
    if not version_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} for contract '{id}' not found.",
        )
    return version_obj


@router.get(
    "/{id}/diff",
    response_model=ContractDiffResponse,
    summary="Compute visual and structural diff between two contract versions",
)
def diff_contract_versions(
    id: str,
    from_version: int = Query(..., ge=1, description="Source base version"),
    to_version: int = Query(..., ge=1, description="Target version to compare against"),
    db: Session = Depends(get_db),
) -> ContractDiffResponse:
    service = ContractService(db)
    try:
        return service.diff_versions(
            contract_id=id,
            from_version=from_version,
            to_version=to_version,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err

