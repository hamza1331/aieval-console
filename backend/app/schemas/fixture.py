"""Golden test fixture schemas (FR-10, FR-16)."""

from typing import Any

from pydantic import BaseModel, Field


class FixtureValidateRequest(BaseModel):
    """Payload to validate an existing or external fixture."""

    fixture: dict[str, Any] = Field(..., description="Fixture JSON object")


class FixtureValidateResponse(BaseModel):
    """Result of fixture validation."""

    valid: bool = Field(..., description="Whether the fixture conforms to the specification")
    error: str | None = Field(default=None, description="Validation failure explanation")
    checks_count: int = Field(default=0, description="Number of valid checks parsed")
