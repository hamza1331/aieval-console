"""Evaluation execution and run history persistence service."""

import uuid
from datetime import datetime
from typing import Any

import aieval
from sqlalchemy.orm import Session

from app.adapters.aieval_adapter import AievalAdapter
from app.models.evaluation_run import EvaluationRun
from app.repositories.contract_repo import ContractRepository
from app.repositories.review_repo import ReviewRepository
from app.repositories.run_repo import RunRepository
from app.schemas.contract import ContractDefinitionSchema
from app.schemas.evaluation import (
    BatchEvaluationResponse,
    BatchItemOutcome,
    EvaluationResponse,
)
from app.schemas.review import ReviewResponse
from app.schemas.run import RunDetailResponse, RunSummaryResponse


class EvaluationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.contract_repo = ContractRepository(db)
        self.run_repo = RunRepository(db)
        self.review_repo = ReviewRepository(db)

    def evaluate_and_persist(
        self,
        output: Any,
        contract_version_id: str | None = None,
        contract_id: str | None = None,
        inline_contract: ContractDefinitionSchema | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> EvaluationResponse:
        checks_spec: list[dict[str, Any]]
        target_version_id: str | None = None
        version_number: int | None = None

        if contract_version_id:
            version_obj = self.contract_repo.get_version_by_id(contract_version_id)
            if not version_obj:
                raise ValueError(f"Contract version '{contract_version_id}' not found.")
            checks_spec = version_obj.definition_json["checks"]
            target_version_id = version_obj.id
            version_number = version_obj.version

        elif contract_id:
            contract_obj = self.contract_repo.get_by_id(contract_id)
            if not contract_obj:
                raise ValueError(f"Contract '{contract_id}' not found.")
            version_obj = self.contract_repo.get_latest_version(contract_id)
            if not version_obj:
                raise ValueError(f"Contract '{contract_id}' has no active versions.")
            checks_spec = version_obj.definition_json["checks"]
            target_version_id = version_obj.id
            version_number = version_obj.version

        elif inline_contract:
            checks_spec = inline_contract.checks
            version_number = 1

        else:
            raise ValueError(
                "Must specify 'contract_version_id', 'contract_id', or inline 'contract'."
            )

        context_data = {"input": input_data} if input_data else None
        initial_run_id = str(uuid.uuid4())

        # Execute evaluation through the adapter
        response = AievalAdapter.evaluate(
            output=output,
            checks_spec=checks_spec,
            context_data=context_data,
            run_id=initial_run_id,
            contract_version=version_number,
        )

        # If evaluating against a registered contract version, persist the run snapshot
        if target_version_id:
            run = self.run_repo.create_run(
                contract_version_id=target_version_id,
                status=response.status,
                input_json=input_data,
                output_json=output,
                result_json=response.model_dump(),
                duration_ms=response.duration_ms,
                aieval_version=getattr(aieval, "__version__", "0.1.1"),
            )
            # Create default linked review record
            self.review_repo.create_review(
                run_id=run.id,
                status="unreviewed",
                note=None,
            )
            self.db.commit()
            response.run_id = run.id

        return response

    def evaluate_batch(
        self,
        items: list[Any],
        contract_version_id: str | None = None,
        contract_id: str | None = None,
        inline_contract: ContractDefinitionSchema | None = None,
    ) -> BatchEvaluationResponse:
        results: list[BatchItemOutcome] = []
        total_duration = 0.0
        passed_count = 0
        failed_count = 0

        for item in items:
            input_val = getattr(item, "input", None)
            output_val = getattr(item, "output", None)
            item_id = getattr(item, "item_id", None)

            res = self.evaluate_and_persist(
                output=output_val,
                contract_version_id=contract_version_id,
                contract_id=contract_id,
                inline_contract=inline_contract,
                input_data=input_val,
            )

            total_duration += res.duration_ms
            if res.status == "passed":
                passed_count += 1
            else:
                failed_count += 1

            results.append(
                BatchItemOutcome(
                    item_id=item_id,
                    run_id=res.run_id,
                    status=res.status,
                    failures=res.failures,
                    warnings=res.warnings,
                    duration_ms=res.duration_ms,
                )
            )

        total_items = len(results)
        pass_rate = round((passed_count / total_items * 100.0), 2) if total_items > 0 else 0.0

        return BatchEvaluationResponse(
            total_items=total_items,
            passed_count=passed_count,
            failed_count=failed_count,
            pass_rate=pass_rate,
            total_duration_ms=round(total_duration, 2),
            results=results,
        )

    def get_run(self, run_id: str) -> RunDetailResponse | None:
        run = self.run_repo.get_by_id(run_id)
        if not run:
            return None

        contract_version = run.contract_version
        contract = contract_version.contract if contract_version else None

        review_resp: ReviewResponse | None = None
        if run.review:
            review_resp = ReviewResponse(
                id=run.review.id,
                run_id=run.review.run_id,
                status=run.review.status,
                note=run.review.note,
                created_at=run.review.created_at,
                updated_at=run.review.updated_at,
            )

        return RunDetailResponse(
            id=run.id,
            contract_id=contract.id if contract else "",
            contract_name=contract.name if contract else "",
            contract_version_id=run.contract_version_id,
            contract_version_number=contract_version.version if contract_version else 1,
            status=run.status,
            input_json=run.input_json,
            output_json=run.output_json,
            result_json=run.result_json,
            duration_ms=run.duration_ms,
            aieval_version=run.aieval_version,
            created_at=run.created_at,
            review=review_resp,
        )

    def list_runs(
        self,
        contract_id: str | None = None,
        status: str | None = None,
        review_status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_duration_ms: float | None = None,
        max_duration_ms: float | None = None,
        failure_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RunSummaryResponse], int]:
        runs: list[EvaluationRun] = self.run_repo.list_runs(
            contract_id=contract_id,
            status=status,
            review_status=review_status,
            from_date=from_date,
            to_date=to_date,
            min_duration_ms=min_duration_ms,
            max_duration_ms=max_duration_ms,
            limit=limit,
            offset=offset,
        )
        total = self.run_repo.count_runs(
            contract_id=contract_id,
            status=status,
            review_status=review_status,
            from_date=from_date,
            to_date=to_date,
            min_duration_ms=min_duration_ms,
            max_duration_ms=max_duration_ms,
        )

        items: list[RunSummaryResponse] = []
        for r in runs:
            version_obj = r.contract_version
            contract_obj = version_obj.contract if version_obj else None
            summary_dict = r.result_json.get("summary", {})
            failures_list = r.result_json.get("failures", [])

            # Apply failure_code filter if specified
            if failure_code:
                fc_upper = failure_code.upper()
                has_code = any(
                    isinstance(f, dict) and f.get("code", "").upper() == fc_upper
                    for f in failures_list
                )
                if not has_code:
                    continue

            items.append(
                RunSummaryResponse(
                    id=r.id,
                    contract_id=contract_obj.id if contract_obj else "",
                    contract_name=contract_obj.name if contract_obj else "",
                    contract_version_id=r.contract_version_id,
                    contract_version_number=version_obj.version if version_obj else 1,
                    status=r.status,
                    failed_checks=summary_dict.get("failed_checks", 0),
                    total_checks=summary_dict.get("total_checks", 0),
                    duration_ms=r.duration_ms,
                    review_status=r.review.status if r.review else "unreviewed",
                    created_at=r.created_at,
                )
            )

        return items, total
