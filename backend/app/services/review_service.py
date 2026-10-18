"""Review annotation service."""

from sqlalchemy.orm import Session

from app.repositories.review_repo import ReviewRepository
from app.repositories.run_repo import RunRepository
from app.schemas.review import ReviewResponse


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.run_repo = RunRepository(db)
        self.review_repo = ReviewRepository(db)

    def update_review(
        self,
        run_id: str,
        status: str | None = None,
        note: str | None = None,
    ) -> ReviewResponse:
        run = self.run_repo.get_by_id(run_id)
        if not run:
            raise ValueError(f"Evaluation run '{run_id}' not found.")

        if status is not None and status not in ("unreviewed", "reviewed"):
            raise ValueError(
                f"Invalid review status '{status}'. Must be 'unreviewed' or 'reviewed'."
            )

        review = self.review_repo.get_by_run_id(run_id)
        if not review:
            review = self.review_repo.create_review(
                run_id=run_id,
                status=status or "unreviewed",
                note=note,
            )
        else:
            review = self.review_repo.update_review(
                review=review,
                status=status,
                note=note,
            )

        self.db.commit()
        self.db.refresh(review)
        return ReviewResponse.model_validate(review)
