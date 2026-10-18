"""Review database access repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_run_id(self, run_id: str) -> Review | None:
        stmt = select(Review).where(Review.run_id == run_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_review(
        self,
        run_id: str,
        status: str = "unreviewed",
        note: str | None = None,
    ) -> Review:
        review = Review(
            run_id=run_id,
            status=status,
            note=note,
        )
        self.db.add(review)
        self.db.flush()
        return review

    def update_review(
        self,
        review: Review,
        status: str | None = None,
        note: str | None = None,
    ) -> Review:
        if status is not None:
            review.status = status
        if note is not None:
            review.note = note
        self.db.add(review)
        self.db.flush()
        return review

