"""Database bootstrap script with automated Alembic migrations and SQLAlchemy seeding."""
import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add backend directory to path if running directly
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
from app.core.retry import calculate_backoff, TRANSIENT_EXCEPTIONS
from app.db.seed_data import seed_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("society.init_db")


def run_alembic_migrations() -> None:
    """Executes Alembic migrations to head programmatically."""
    alembic_ini_path = backend_dir / "alembic.ini"
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at: {alembic_ini_path}")

    logger.info("=" * 70)
    logger.info("Executing Alembic Migration Engine")
    logger.info(f"Config: {alembic_ini_path}")
    logger.info("=" * 70)

    start_time = time.perf_counter()
    alembic_cfg = Config(str(alembic_ini_path))
    command.upgrade(alembic_cfg, "head")
    elapsed = time.perf_counter() - start_time
    logger.info(f"Alembic migrations upgraded to head in {elapsed:.2f}s.")


async def verify_tables() -> list[str]:
    """Queries PostgreSQL information_schema to verify created tables."""
    query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    async with engine.connect() as conn:
        result = await conn.execute(query)
        tables = [row[0] for row in result.fetchall()]
        return tables


async def verify_indexes() -> list[str]:
    """Queries PostgreSQL pg_indexes to verify created custom indexes."""
    query = text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
        ORDER BY indexname;
    """)
    async with engine.connect() as conn:
        result = await conn.execute(query)
        indexes = [row[0] for row in result.fetchall()]
        return indexes


async def seed_and_verify(with_seeds: bool = True, check_only: bool = False) -> None:
    """Performs seeding and post-migration verification."""
    tables = await verify_tables()
    indexes = await verify_indexes()

    if check_only:
        logger.info(f"Check-only mode: Found {len(tables)} tables and {len(indexes)} indexes.")
        return

    if with_seeds:
        logger.info("Applying SQLAlchemy seed data...")
        await seed_database()

    # Post-execution verification
    tables = await verify_tables()
    indexes = await verify_indexes()

    logger.info("=" * 70)
    logger.info("Database Bootstrap Complete & Verified via Alembic & SQLAlchemy!")
    logger.info(f"Total Public Tables Verified ({len(tables)}):")
    for tbl in tables:
        logger.info(f"  • {tbl}")
    logger.info(f"Total Performance Indexes Verified ({len(indexes)}):")
    for idx in indexes:
        logger.info(f"  • {idx}")
    logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Society Database Initialization Runner (Alembic + SQLAlchemy)")
    parser.add_argument("--no-seeds", action="store_true", help="Do not run SQLAlchemy seeds")
    parser.add_argument("--check-only", action="store_true", help="Only verify existing tables and indexes without running migrations")
    args = parser.parse_args()

    try:
        if not args.check_only:
            # 1. Run Alembic migrations
            run_alembic_migrations()

        # 2. Seed and verify
        asyncio.run(seed_and_verify(with_seeds=not args.no_seeds, check_only=args.check_only))
    except KeyboardInterrupt:
        logger.warning("Database initialization aborted by user.")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Fatal error during database initialization: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
