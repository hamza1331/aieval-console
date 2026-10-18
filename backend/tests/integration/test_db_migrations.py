"""Integration test for Alembic migrations."""

from alembic.config import Config

from alembic import command


def test_alembic_migrations_upgrade_and_downgrade(test_db_path: str) -> None:
    """Verifies that all migrations can upgrade to head and downgrade cleanly."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{test_db_path}")

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Downgrade back to base
    command.downgrade(alembic_cfg, "base")

    # Re-upgrade to head to leave in clean state
    command.upgrade(alembic_cfg, "head")
