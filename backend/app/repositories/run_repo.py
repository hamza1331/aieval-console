"""EvaluationRun database access repository."""

from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.contract_version import ContractVersion
from app.models.evaluation_run import EvaluationRun
from app.models.review import Review


class RunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self,
        contract_version_id: str,
        status: str,
        input_json: dict[str, Any] | None,
        output_json: Any,
        result_json: dict[str, Any],
        duration_ms: float,
        aieval_version: str,
    ) -> EvaluationRun:
        run = EvaluationRun(
            contract_version_id=contract_version_id,
            status=status,
            input_json=input_json,
            output_json=output_json,
            result_json=result_json,
            duration_ms=duration_ms,
            aieval_version=aieval_version,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def get_by_id(self, run_id: str) -> EvaluationRun | None:
        stmt = (
            select(EvaluationRun)
            .where(EvaluationRun.id == run_id)
            .options(
                selectinload(EvaluationRun.contract_version).selectinload(ContractVersion.contract),
                selectinload(EvaluationRun.review),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_runs(
        self,
        contract_id: str | None = None,
        status: str | None = None,
        review_status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_duration_ms: float | None = None,
        max_duration_ms: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvaluationRun]:
        stmt = select(EvaluationRun).options(
            selectinload(EvaluationRun.contract_version).selectinload(ContractVersion.contract),
            selectinload(EvaluationRun.review),
        )

        if contract_id:
            stmt = stmt.join(ContractVersion).where(ContractVersion.contract_id == contract_id)
        if review_status:
            stmt = stmt.join(Review, EvaluationRun.id == Review.run_id).where(
                Review.status == review_status
            )
        if status:
            stmt = stmt.where(EvaluationRun.status == status)
        if from_date:
            stmt = stmt.where(EvaluationRun.created_at >= from_date)
        if to_date:
            stmt = stmt.where(EvaluationRun.created_at <= to_date)
        if min_duration_ms is not None:
            stmt = stmt.where(EvaluationRun.duration_ms >= min_duration_ms)
        if max_duration_ms is not None:
            stmt = stmt.where(EvaluationRun.duration_ms <= max_duration_ms)

        stmt = stmt.order_by(desc(EvaluationRun.created_at)).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count_runs(
        self,
        contract_id: str | None = None,
        status: str | None = None,
        review_status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_duration_ms: float | None = None,
        max_duration_ms: float | None = None,
    ) -> int:
        stmt = select(func.count(EvaluationRun.id))
        if contract_id:
            stmt = stmt.join(ContractVersion).where(ContractVersion.contract_id == contract_id)
        if review_status:
            stmt = stmt.join(Review, EvaluationRun.id == Review.run_id).where(
                Review.status == review_status
            )
        if status:
            stmt = stmt.where(EvaluationRun.status == status)
        if from_date:
            stmt = stmt.where(EvaluationRun.created_at >= from_date)
        if to_date:
            stmt = stmt.where(EvaluationRun.created_at <= to_date)
        if min_duration_ms is not None:
            stmt = stmt.where(EvaluationRun.duration_ms >= min_duration_ms)
        if max_duration_ms is not None:
            stmt = stmt.where(EvaluationRun.duration_ms <= max_duration_ms)
        return self.db.execute(stmt).scalar() or 0
