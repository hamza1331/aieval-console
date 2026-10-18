"""Declarative contract schemas."""

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
