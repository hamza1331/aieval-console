"""EvaluationRun ORM model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.contract_version import ContractVersion
    from app.models.review import Review


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    contract_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contract_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    input_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_json: Mapped[Any] = mapped_column(JSON, nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    aieval_version: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True,
    )

    # Relationships
    contract_version: Mapped["ContractVersion"] = relationship(
        "ContractVersion",
        back_populates="runs",
    )
    review: Mapped["Review | None"] = relationship(
        "Review",
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )
