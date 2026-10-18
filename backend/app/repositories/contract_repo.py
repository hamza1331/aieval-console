"""Contract and ContractVersion database access repository."""

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.contract import Contract
from app.models.contract_version import ContractVersion


class ContractRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_contract(
        self,
        name: str,
        description: str | None = None,
        status: str = "active",
    ) -> Contract:
        contract = Contract(
            name=name,
            description=description,
            status=status,
        )
        self.db.add(contract)
        self.db.flush()
        return contract

    def get_by_id(self, contract_id: str) -> Contract | None:
        stmt = (
            select(Contract)
            .where(Contract.id == contract_id)
            .options(selectinload(Contract.versions))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_contracts(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Contract]:
        stmt = select(Contract).options(selectinload(Contract.versions))
        if status:
            stmt = stmt.where(Contract.status == status)
        stmt = stmt.order_by(desc(Contract.created_at)).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count_contracts(self, status: str | None = None) -> int:
        stmt = select(func.count(Contract.id))
        if status:
            stmt = stmt.where(Contract.status == status)
        return self.db.execute(stmt).scalar() or 0

    def update_contract(
        self,
        contract: Contract,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Contract:
        if name is not None:
            contract.name = name
        if description is not None:
            contract.description = description
        if status is not None:
            contract.status = status
        self.db.add(contract)
        self.db.flush()
        return contract

    def create_version(
        self,
        contract_id: str,
        version: int,
        definition_json: dict[str, Any],
        definition_hash: str,
    ) -> ContractVersion:
        contract_version = ContractVersion(
            contract_id=contract_id,
            version=version,
            definition_json=definition_json,
            definition_hash=definition_hash,
        )
        self.db.add(contract_version)
        self.db.flush()
        return contract_version

    def get_version_by_id(self, version_id: str) -> ContractVersion | None:
        stmt = (
            select(ContractVersion)
            .where(ContractVersion.id == version_id)
            .options(selectinload(ContractVersion.contract))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_version_by_number(self, contract_id: str, version: int) -> ContractVersion | None:
        stmt = (
            select(ContractVersion)
            .where(
                ContractVersion.contract_id == contract_id,
                ContractVersion.version == version,
            )
            .options(selectinload(ContractVersion.contract))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_latest_version(self, contract_id: str) -> ContractVersion | None:
        stmt = (
            select(ContractVersion)
            .where(ContractVersion.contract_id == contract_id)
            .order_by(desc(ContractVersion.version))
            .limit(1)
            .options(selectinload(ContractVersion.contract))
        )
        return self.db.execute(stmt).scalar_one_or_none()

