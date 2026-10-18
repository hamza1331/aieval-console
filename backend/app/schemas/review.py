"""Review schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReviewUpdateRequest(BaseModel):
    """Payload to update review note and status."""

    status: str | None = Field(default=None, description="Status: 'unreviewed' or 'reviewed'")
    note: str | None = Field(default=None, description="Human annotation note")


class ReviewResponse(BaseModel):
    """Serialized review status and annotation."""

    id: str
    run_id: str
    status: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
