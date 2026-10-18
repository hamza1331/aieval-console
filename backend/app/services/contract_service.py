"""Contract and ContractVersion business logic service."""

import hashlib
import json
from typing import Any

import aieval
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.repositories.contract_repo import ContractRepository
from app.schemas.contract import (
    ContractDetailResponse,
    ContractSummaryResponse,
    ContractVersionResponse,
)


def _compute_hash(definition: dict[str, Any]) -> str:
    canonical = json.dumps(definition, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_checks(checks: list[dict[str, Any]]) -> None:
    if not checks:
        raise ValueError("Contract definition must specify at least one check.")
    for check_spec in checks:
        # Validates that check can be instantiated by aieval-py
        aieval.build_check_from_spec(check_spec)


def _to_detail_response(contract: Contract) -> ContractDetailResponse:
    versions = [
        ContractVersionResponse(
            id=v.id,
            contract_id=v.contract_id,
            version=v.version,
            definition_json=v.definition_json,
            definition_hash=v.definition_hash,
            created_at=v.created_at,
        )
        for v in contract.versions
    ]
    return ContractDetailResponse(
        id=contract.id,
        name=contract.name,
        description=contract.description,
        status=contract.status,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        versions=versions,
    )


class ContractService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ContractRepository(db)

    def create_contract(
        self,
        name: str,
        description: str | None,
        checks: list[dict[str, Any]],
    ) -> ContractDetailResponse:
        _validate_checks(checks)

        definition_json = {
            "name": name,
            "description": description,
            "checks": checks,
        }
        definition_hash = _compute_hash(definition_json)

        contract = self.repo.create_contract(
            name=name,
            description=description,
            status="active",
        )
        self.repo.create_version(
            contract_id=contract.id,
            version=1,
            definition_json=definition_json,
            definition_hash=definition_hash,
        )
        self.db.commit()
        self.db.refresh(contract)
        return _to_detail_response(contract)

    def create_new_version(
        self,
        contract_id: str,
        checks: list[dict[str, Any]],
    ) -> ContractVersionResponse:
        contract = self.repo.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract '{contract_id}' not found.")
        if contract.status == "archived":
            raise ValueError(f"Cannot add versions to archived contract '{contract_id}'.")

        _validate_checks(checks)

        latest = self.repo.get_latest_version(contract_id)
        next_version = (latest.version + 1) if latest else 1

        definition_json = {
            "name": contract.name,
            "description": contract.description,
            "checks": checks,
        }
        definition_hash = _compute_hash(definition_json)

        version = self.repo.create_version(
            contract_id=contract_id,
            version=next_version,
            definition_json=definition_json,
            definition_hash=definition_hash,
        )
        self.db.commit()
        return ContractVersionResponse.model_validate(version)

    def get_contract(self, contract_id: str) -> ContractDetailResponse | None:
        contract = self.repo.get_by_id(contract_id)
        if not contract:
            return None
        return _to_detail_response(contract)

    def list_contracts(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ContractSummaryResponse], int]:
        contracts = self.repo.list_contracts(status=status, limit=limit, offset=offset)
        total = self.repo.count_contracts(status=status)

        items = [
            ContractSummaryResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                status=c.status,
                latest_version=c.versions[0].version if c.versions else 1,
                total_versions=len(c.versions),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in contracts
        ]
        return items, total

    def update_contract(
        self,
        contract_id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> ContractDetailResponse | None:
        contract = self.repo.get_by_id(contract_id)
        if not contract:
            return None

        if status is not None and status not in ("active", "archived"):
            raise ValueError(f"Invalid status '{status}'. Must be 'active' or 'archived'.")

        updated = self.repo.update_contract(
            contract=contract,
            name=name,
            description=description,
            status=status,
        )
        self.db.commit()
        self.db.refresh(updated)
        return _to_detail_response(updated)

    def get_version(self, contract_id: str, version_number: int) -> ContractVersionResponse | None:
        version = self.repo.get_version_by_number(contract_id, version_number)
        if not version:
            return None
        return ContractVersionResponse.model_validate(version)
