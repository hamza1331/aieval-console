"""Database migration runner using Alembic."""

from pathlib import Path

from alembic.config import Config

from alembic import command
from app.core.config import settings
from app.core.logging import logger


def run_migrations() -> None:
    """Runs Alembic migrations to upgrade database to head."""
    # Find alembic.ini
    possible_paths = [
        Path("alembic.ini"),
        Path(__file__).resolve().parent.parent.parent / "alembic.ini",
        Path("/app/backend/alembic.ini"),
    ]

    ini_path: Path | None = None
    for p in possible_paths:
        if p.is_file():
            ini_path = p
            break

    if not ini_path:
        raise FileNotFoundError("Could not find alembic.ini; refusing to skip database migrations.")

    logger.info(f"Running database migrations using config: {ini_path}")
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations successfully applied.")


if __name__ == "__main__":
    run_migrations()
