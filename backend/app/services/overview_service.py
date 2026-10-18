"""Overview statistics service (FR-11)."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.evaluation_run import EvaluationRun
from app.models.review import Review
from app.schemas.overview import OverviewResponse
from app.services.evaluation_service import EvaluationService


class OverviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.eval_service = EvaluationService(db)

    def get_overview(self) -> OverviewResponse:
        """Calculates high-level metrics and returns the 10 most recent runs."""
        # 1. Contract counts
        total_contracts = self.db.execute(select(func.count(Contract.id))).scalar() or 0
        active_contracts = (
            self.db.execute(
                select(func.count(Contract.id)).where(Contract.status == "active")
            ).scalar()
            or 0
        )

        # 2. Run counts
        total_runs = self.db.execute(select(func.count(EvaluationRun.id))).scalar() or 0
        passed_runs = (
            self.db.execute(
                select(func.count(EvaluationRun.id)).where(EvaluationRun.status == "passed")
            ).scalar()
            or 0
        )
        failed_runs = (
            self.db.execute(
                select(func.count(EvaluationRun.id)).where(EvaluationRun.status == "failed")
            ).scalar()
            or 0
        )

        pass_rate = round((passed_runs / total_runs * 100), 1) if total_runs > 0 else 100.0

        # 3. Unreviewed failures
        unreviewed_stmt = (
            select(func.count(EvaluationRun.id))
            .join(Review, Review.run_id == EvaluationRun.id, isouter=True)
            .where(EvaluationRun.status == "failed")
            .where(or_(Review.status == "unreviewed", Review.status.is_(None)))
        )
        unreviewed_failures = self.db.execute(unreviewed_stmt).scalar() or 0

        # 4. Recent runs
        recent_runs, _ = self.eval_service.list_runs(limit=10, offset=0)

        return OverviewResponse(
            total_contracts=total_contracts,
            active_contracts=active_contracts,
            total_runs=total_runs,
            passed_runs=passed_runs,
            failed_runs=failed_runs,
            pass_rate=pass_rate,
            unreviewed_failures=unreviewed_failures,
            recent_runs=recent_runs,
        )
