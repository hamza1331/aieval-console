"""Health check schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service readiness status")
    app_version: str = Field(..., description="Application version")
    aieval_version: str = Field(..., description="Integrated aieval-py library version")
