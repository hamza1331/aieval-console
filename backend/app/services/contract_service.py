"""Contract and ContractVersion business logic service."""

import hashlib
import json
from typing import Any

import aieval
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.repositories.contract_repo import ContractRepository
from app.schemas.contract import (
    CheckDiffItem,
    ContractDetailResponse,
    ContractDiffResponse,
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

    def diff_versions(
        self,
        contract_id: str,
        from_version: int,
        to_version: int,
    ) -> ContractDiffResponse:
        v1 = self.repo.get_version_by_number(contract_id, from_version)
        if not v1:
            raise ValueError(f"Contract version {from_version} not found.")

        v2 = self.repo.get_version_by_number(contract_id, to_version)
        if not v2:
            raise ValueError(f"Contract version {to_version} not found.")

        checks_v1: list[dict[str, Any]] = v1.definition_json.get("checks", [])
        checks_v2: list[dict[str, Any]] = v2.definition_json.get("checks", [])

        # Match checks by (type, field) signature or index
        def check_key(c: dict[str, Any], idx: int) -> tuple[str, str | None, int]:
            return (c.get("type", ""), c.get("field"), idx)

        # Build diff items
        diff_items: list[CheckDiffItem] = []
        added_count = 0
        removed_count = 0
        modified_count = 0
        unchanged_count = 0

        # Create lookup by (type, field) for matching
        v1_matched = set()
        v2_matched = set()

        for i, c1 in enumerate(checks_v1):
            c1_type = c1.get("type", "")
            c1_field = c1.get("field")

            # Try to find corresponding check in v2
            match_idx = None
            for j, c2 in enumerate(checks_v2):
                if j in v2_matched:
                    continue
                if c2.get("type") == c1_type and c2.get("field") == c1_field:
                    match_idx = j
                    break

            if match_idx is not None:
                v1_matched.add(i)
                v2_matched.add(match_idx)
                c2 = checks_v2[match_idx]

                if c1 == c2:
                    unchanged_count += 1
                    diff_items.append(
                        CheckDiffItem(
                            check_type=c1_type,
                            field=c1_field,
                            change_type="unchanged",
                            old_spec=c1,
                            new_spec=c2,
                        )
                    )
                else:
                    modified_count += 1
                    details: list[str] = []
                    all_keys = set(c1.keys()).union(set(c2.keys()))
                    for k in sorted(all_keys):
                        if k not in c1:
                            details.append(f"Added attribute '{k}': {c2[k]}")
                        elif k not in c2:
                            details.append(f"Removed attribute '{k}': {c1[k]}")
                        elif c1[k] != c2[k]:
                            details.append(f"Changed '{k}' from {c1[k]} to {c2[k]}")

                    diff_items.append(
                        CheckDiffItem(
                            check_type=c1_type,
                            field=c1_field,
                            change_type="modified",
                            old_spec=c1,
                            new_spec=c2,
                            details=details,
                        )
                    )
            else:
                removed_count += 1
                diff_items.append(
                    CheckDiffItem(
                        check_type=c1_type,
                        field=c1_field,
                        change_type="removed",
                        old_spec=c1,
                        new_spec=None,
                        details=[f"Removed check: {c1_type} on field '{c1_field}'"],
                    )
                )

        # Any unmatched checks in v2 are added
        for j, c2 in enumerate(checks_v2):
            if j not in v2_matched:
                added_count += 1
                c2_type = c2.get("type", "")
                c2_field = c2.get("field")
                diff_items.append(
                    CheckDiffItem(
                        check_type=c2_type,
                        field=c2_field,
                        change_type="added",
                        old_spec=None,
                        new_spec=c2,
                        details=[f"Added check: {c2_type} on field '{c2_field}'"],
                    )
                )

        return ContractDiffResponse(
            contract_id=contract_id,
            from_version=from_version,
            to_version=to_version,
            added_count=added_count,
            removed_count=removed_count,
            modified_count=modified_count,
            unchanged_count=unchanged_count,
            checks=diff_items,
        )
