"""Declarative contract schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CheckSpecSchema(BaseModel):
    """Specification of an individual check in a declarative contract."""

    type: str = Field(
        ..., description="Check type or alias, e.g. required_fields, enum, max_length"
    )
    field: str | None = Field(default=None, description="Optional target field path")
    severity: str | None = Field(
        default="error", description="Failure severity: info, warning, error, critical"
    )

    # Dynamic attributes for check configuration (fields, allowed, max, min, pattern, etc.)
    model_config = {"extra": "allow"}


class ContractDefinitionSchema(BaseModel):
    """Declarative validation contract definition."""

    name: str = Field(
        ..., min_length=1, max_length=200, description="Name of the validation contract"
    )
    description: str | None = Field(default=None, description="Description of validation purpose")
    checks: list[dict[str, Any]] = Field(
        ..., min_length=1, description="List of declarative check specifications"
    )


class ContractCreateRequest(BaseModel):
    """Payload to create a contract with an initial version 1."""

    name: str = Field(
        ..., min_length=1, max_length=200, description="Name of the validation contract"
    )
    description: str | None = Field(default=None, description="Optional description")
    checks: list[dict[str, Any]] = Field(
        ..., min_length=1, description="List of declarative check specifications"
    )


class ContractUpdateRequest(BaseModel):
    """Payload to update contract metadata or status (archive)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None)
    status: str | None = Field(default=None, description="Status: 'active' or 'archived'")


class ContractVersionCreateRequest(BaseModel):
    """Payload to create a new sequential immutable contract version."""

    checks: list[dict[str, Any]] = Field(
        ..., min_length=1, description="List of declarative check specifications"
    )


class ContractVersionResponse(BaseModel):
    """Serialized contract version definition."""

    id: str
    contract_id: str
    version: int
    definition_json: dict[str, Any]
    definition_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractSummaryResponse(BaseModel):
    """Lightweight contract metadata for lists."""

    id: str
    name: str
    description: str | None = None
    status: str
    latest_version: int
    total_versions: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractDetailResponse(BaseModel):
    """Full contract details including full version history."""

    id: str
    name: str
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    versions: list[ContractVersionResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CheckDiffItem(BaseModel):
    """Difference comparison item for an individual check."""

    check_type: str
    field: str | None = None
    change_type: str = Field(..., description="'added' | 'removed' | 'modified' | 'unchanged'")
    old_spec: dict[str, Any] | None = None
    new_spec: dict[str, Any] | None = None
    details: list[str] = Field(default_factory=list)


class ContractDiffResponse(BaseModel):
    """Structured comparison between two contract versions."""

    contract_id: str
    from_version: int
    to_version: int
    added_count: int
    removed_count: int
    modified_count: int
    unchanged_count: int
    checks: list[CheckDiffItem]
