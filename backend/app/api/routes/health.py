"""Health check route."""

import aieval
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns application health and version information without leaking secrets (FR-14)."""
    return HealthResponse(
        status="ok",
        app_version=settings.VERSION,
        aieval_version=getattr(aieval, "__version__", "0.1.1"),
    )
