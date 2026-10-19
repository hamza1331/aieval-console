"""Tests for migration and application startup failure handling."""

import asyncio

import pytest

from app import main
from app.core.config import settings
from app.db import migrate


def test_migrations_fail_if_alembic_config_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(migrate.Path, "is_file", lambda self: False)

    with pytest.raises(FileNotFoundError, match="refusing to skip database migrations"):
        migrate.run_migrations()


def test_startup_propagates_migration_failure(monkeypatch) -> None:
    monkeypatch.setattr(settings, "AUTO_MIGRATE", True)

    def fail_migrations() -> None:
        raise RuntimeError("migration failed")

    monkeypatch.setattr(main, "run_migrations", fail_migrations)

    async def run_lifespan() -> None:
        async with main.lifespan(main.app):
            pass

    with pytest.raises(RuntimeError, match="migration failed"):
        asyncio.run(run_lifespan())
