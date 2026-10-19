"""Health check route."""

import aieval
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Returns application health and version information without leaking secrets (FR-14)."""
    try:
        db.execute(text("SELECT 1 FROM contracts LIMIT 1"))
    except SQLAlchemyError as exc:
        logger.error(f"Health check database query failed: {exc}")
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc

    return HealthResponse(
        status="ok",
        app_version=settings.VERSION,
        aieval_version=aieval.__version__,
    )
