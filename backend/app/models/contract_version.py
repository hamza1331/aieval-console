"""ContractVersion ORM model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.evaluation_run import EvaluationRun


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ContractVersion(Base):
    __tablename__ = "contract_versions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    contract_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    __table_args__ = (UniqueConstraint("contract_id", "version", name="uq_contract_version"),)

    # Relationships
    contract: Mapped["Contract"] = relationship("Contract", back_populates="versions")
    runs: Mapped[list["EvaluationRun"]] = relationship(
        "EvaluationRun",
        back_populates="contract_version",
        cascade="all, delete-orphan",
    )
