"""Evaluations route."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.adapters.aieval_adapter import AievalAdapter
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse

router = APIRouter(tags=["evaluations"])

# In-memory registry for Phase 1 integration spike (Week 1)
# Demonstrates Appendix A contract before full database persistence in Week 2
DEMO_CONTRACT_VERSION_ID = "demo-support-ticket-v1"

IN_MEMORY_CONTRACTS: dict[str, dict[str, Any]] = {
    DEMO_CONTRACT_VERSION_ID: {
        "version": 1,
        "name": "Support ticket classification",
        "description": "Validate structured output from a ticket classifier",
        "checks": [
            {
                "type": "required_fields",
                "fields": ["category", "priority", "summary"],
            },
            {
                "type": "enum",
                "field": "category",
                "allowed": ["billing", "technical", "account", "other"],
            },
            {
                "type": "enum",
                "field": "priority",
                "allowed": ["low", "normal", "high", "urgent"],
            },
            {
                "type": "max_length",
                "field": "summary",
                "max": 300,
            },
        ],
    }
}


@router.post(
    "/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate output payload against a contract",
)
def evaluate_output(request: EvaluationRequest) -> EvaluationResponse:
    """Evaluates an AI output payload against a contract version or inline definition (FR-04)."""
    checks_spec: list[dict[str, Any]]
    contract_version: int | None = None

    if request.contract is not None:
        checks_spec = request.contract.checks
        contract_version = 1
    elif request.contract_version_id is not None:
        contract_data = IN_MEMORY_CONTRACTS.get(request.contract_version_id)
        if not contract_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract version '{request.contract_version_id}' not found.",
            )
        checks_spec = contract_data["checks"]
        contract_version = contract_data.get("version", 1)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either 'contract_version_id' or inline 'contract' definition.",
        )

    try:
        run_id = str(uuid.uuid4())
        context_data = {"input": request.input} if request.input else None
        return AievalAdapter.evaluate(
            output=request.output,
            checks_spec=checks_spec,
            context_data=context_data,
            run_id=run_id,
            contract_version=contract_version,
        )
    except (ValueError, TypeError) as err:
        # Reject malformed contract checks with 422 (FR-02)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid contract check specification: {err}",
        ) from err
