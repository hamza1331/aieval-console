"""Database demo data seeder (FR-13).

Can be executed as a repeatable CLI command:
    python -m app.db.seed
"""

import sys
from typing import Any

from app.db.session import SessionLocal
from app.services.contract_service import ContractService
from app.services.evaluation_service import EvaluationService
from app.services.review_service import ReviewService

APPENDIX_A_CHECKS: list[dict[str, Any]] = [
    {
        "type": "required_fields",
        "fields": ["category", "priority", "summary"],
    },
    {
        "type": "enum",
        "field": "category",
        "allowed": ["billing", "technical", "account", "other"],
    },
    {
        "type": "enum",
        "field": "priority",
        "allowed": ["low", "normal", "high", "urgent"],
    },
    {
        "type": "max_length",
        "field": "summary",
        "max": 300,
    },
]


def seed_database(force: bool = False) -> bool:
    """Seeds the database with the Appendix A contract and realistic synthetic runs."""
    db = SessionLocal()
    try:
        contract_service = ContractService(db)
        eval_service = EvaluationService(db)
        review_service = ReviewService(db)

        # Check idempotency
        contracts, _ = contract_service.list_contracts(limit=10)
        existing_demo = next(
            (c for c in contracts if c.name == "Support ticket classification"),
            None,
        )

        if existing_demo and not force:
            print("Demo contract 'Support ticket classification' already exists. Skipping seed.")
            return False

        print("Seeding demo contract 'Support ticket classification'...")
        contract = contract_service.create_contract(
            name="Support ticket classification",
            description="Validate structured output from a ticket classifier (Appendix A demo)",
            checks=APPENDIX_A_CHECKS,
        )
        version_id = contract.versions[0].id
        print(f"Created contract {contract.id} with version {version_id}.")

        # Synthetic runs
        synthetic_cases: list[dict[str, Any]] = [
            {
                "input": {"task": "classify_support_ticket", "ticket_id": "TICK-101"},
                "output": {
                    "category": "billing",
                    "priority": "urgent",
                    "summary": "Payment method expired for annual enterprise subscription renewal.",
                },
                "review": None,
            },
            {
                "input": {"task": "classify_support_ticket", "ticket_id": "TICK-102"},
                "output": {
                    "category": "technical",
                    "priority": "normal",
                    "summary": "User unable to upload profile avatar PNG in settings.",
                },
                "review": None,
            },
            {
                "input": {"task": "classify_support_ticket", "ticket_id": "TICK-103"},
                "output": {
                    "category": "technical",
                    "priority": "super_urgent_now",  # Invalid enum
                    "summary": "Database connectivity loss in production cluster.",
                },
                "review": {
                    "status": "reviewed",
                    "note": "Model hallucinated non-standard priority string. Needs prompt constraint adjustment.",
                },
            },
            {
                "input": {"task": "classify_support_ticket", "ticket_id": "TICK-104"},
                "output": {
                    "category": "account",
                    "priority": "low",
                    # Missing summary
                },
                "review": None,
            },
            {
                "input": {"task": "classify_support_ticket", "ticket_id": "TICK-105"},
                "output": {
                    "category": "other",
                    "priority": "low",
                    "summary": "Repeated explanation " * 25,  # Exceeds 300 chars
                },
                "review": None,
            },
        ]

        print("Generating synthetic evaluation runs...")
        for idx, case in enumerate(synthetic_cases, 1):
            resp = eval_service.evaluate_and_persist(
                contract_version_id=version_id,
                input_data=case["input"],
                output=case["output"],
            )
            print(f"  Run {idx}: status={resp.status} (run_id={resp.run_id})")

            review_info = case.get("review")
            if review_info:
                review_service.update_review(
                    run_id=resp.run_id,
                    status=review_info["status"],
                    note=review_info["note"],
                )
                print(f"  Annotated Run {idx} with review note.")

        print("Demo seeding complete!")
        return True
    finally:
        db.close()


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    seed_database(force=force_flag)
