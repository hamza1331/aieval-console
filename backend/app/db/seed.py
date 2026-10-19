"""Database demo data seeder (FR-13, Phase 5 Multi-Domain).

Seeds the database with all 3 official SRS demonstration domains:
1. Support ticket classification (Appendix A)
2. Recruitment candidate screening (SRS Sec 3.2)
3. Invoice data extraction (SRS Sec 3.2)

Can be executed as a repeatable CLI command:
    python -m app.db.seed
"""

import sys
from typing import Any

from app.db.session import SessionLocal
from app.services.contract_service import ContractService
from app.services.evaluation_service import EvaluationService
from app.services.review_service import ReviewService

SUPPORT_TICKET_CHECKS: list[dict[str, Any]] = [
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

RECRUITMENT_CHECKS: list[dict[str, Any]] = [
    {
        "type": "required_fields",
        "fields": ["candidate_name", "recommendation", "score"],
    },
    {
        "type": "enum",
        "field": "recommendation",
        "allowed": ["advance", "hold", "reject"],
    },
    {
        "type": "numeric_range",
        "field": "score",
        "min": 0,
        "max": 100,
    },
]

INVOICE_CHECKS: list[dict[str, Any]] = [
    {
        "type": "required_fields",
        "fields": ["invoice_number", "currency", "total_amount", "invoice_date"],
    },
    {
        "type": "regex_match",
        "field": "invoice_number",
        "pattern": r"^INV-[0-9]{5}$",
    },
    {
        "type": "enum",
        "field": "currency",
        "allowed": ["USD", "EUR", "GBP"],
    },
    {
        "type": "numeric_range",
        "field": "total_amount",
        "min": 0.01,
    },
]


def seed_database(force: bool = False) -> bool:
    """Seeds the database with contracts and synthetic runs across all 3 domains."""
    db = SessionLocal()
    try:
        contract_service = ContractService(db)
        eval_service = EvaluationService(db)
        review_service = ReviewService(db)

        # Check idempotency
        contracts, _ = contract_service.list_contracts(limit=20)
        existing_names = {c.name for c in contracts}

        # 1. Seed Support Ticket Classifier
        if "Support ticket classification" not in existing_names or force:
            print("Seeding domain 1: 'Support ticket classification'...")
            c1 = contract_service.create_contract(
                name="Support ticket classification",
                description="Validate structured output from a ticket classifier (Appendix A demo)",
                checks=SUPPORT_TICKET_CHECKS,
            )
            v1_id = c1.versions[0].id

            # Passing run
            eval_service.evaluate_and_persist(
                contract_version_id=v1_id,
                input_data={"prompt": "Customer unable to pay invoice due to expired credit card."},
                output={
                    "category": "billing",
                    "priority": "urgent",
                    "summary": "Customer unable to complete monthly invoice payment with credit card.",
                },
            )
            # Failing run with review
            r_fail = eval_service.evaluate_and_persist(
                contract_version_id=v1_id,
                input_data={"prompt": "Urgent assistance required with database connection pool."},
                output={
                    "category": "technical",
                    "priority": "immediate_now",
                    "summary": "Database connectivity intermittent on primary cluster.",
                },
            )
            review_service.update_review(
                run_id=r_fail.run_id,
                status="reviewed",
                note="Model hallucinated non-standard priority 'immediate_now'. Added fixture to regression suite.",
            )

        # 2. Seed Recruitment Candidate Screening
        if "Recruitment candidate screening" not in existing_names or force:
            print("Seeding domain 2: 'Recruitment candidate screening'...")
            c2 = contract_service.create_contract(
                name="Recruitment candidate screening",
                description="Validate candidate triage summary, skills array, and evaluation rating (SRS Sec 3.2)",
                checks=RECRUITMENT_CHECKS,
            )
            v2_id = c2.versions[0].id

            eval_service.evaluate_and_persist(
                contract_version_id=v2_id,
                input_data={"role": "Senior Backend Engineer", "candidate": "Alice Johnson"},
                output={
                    "candidate_name": "Alice Johnson",
                    "recommendation": "advance",
                    "score": 94,
                },
            )
            eval_service.evaluate_and_persist(
                contract_version_id=v2_id,
                input_data={"role": "Junior Data Analyst", "candidate": "Bob Vance"},
                output={
                    "candidate_name": "Bob Vance",
                    "recommendation": "strong_hire",
                    "score": 120,
                },
            )

        # 3. Seed Invoice Data Extraction
        if "Invoice data extraction" not in existing_names or force:
            print("Seeding domain 3: 'Invoice data extraction'...")
            c3 = contract_service.create_contract(
                name="Invoice data extraction",
                description="Validate invoice ID formatting, supported currency, and positive amount (SRS Sec 3.2)",
                checks=INVOICE_CHECKS,
            )
            v3_id = c3.versions[0].id

            eval_service.evaluate_and_persist(
                contract_version_id=v3_id,
                input_data={"raw_ocr": "Invoice INV-44912 from ACME Corp. Amount: $1,250.00"},
                output={
                    "invoice_number": "INV-44912",
                    "currency": "USD",
                    "total_amount": 1250.00,
                    "invoice_date": "2026-10-12",
                },
            )

        db.commit()
        print("Demo database seeding successfully completed.")
        return True

    finally:
        db.close()


if __name__ == "__main__":
    force_flag = "--force" in sys.argv or "-f" in sys.argv
    seed_database(force=force_flag)
