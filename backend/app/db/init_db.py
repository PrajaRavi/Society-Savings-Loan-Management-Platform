"""Database bootstrap script with automated exponential back-off and retry resilience."""
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

from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
from app.core.retry import calculate_backoff, TRANSIENT_EXCEPTIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("society.init_db")


def read_sql_file(file_path: Path) -> str:
    """Reads SQL file contents safely."""
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found at: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


async def execute_sql_script(sql_content: str, description: str) -> None:
    """Executes SQL script using underlying asyncpg connection (simple query protocol) with exponential back-off."""
    max_retries = settings.DB_MAX_RETRIES
    base_delay = settings.DB_RETRY_BASE_DELAY
    max_delay = settings.DB_RETRY_MAX_DELAY

    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to database to apply {description} (Attempt {attempt + 1}/{max_retries})...")
            start_time = time.perf_counter()
            async with engine.begin() as conn:
                raw_conn = await conn.get_raw_connection()
                # asyncpg's driver connection execute supports multi-statement SQL strings
                if hasattr(raw_conn, "driver_connection"):
                    await raw_conn.driver_connection.execute(sql_content)
                else:
                    # Fallback statement splitting
                    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
                    for stmt in statements:
                        await conn.execute(text(stmt))
            elapsed = time.perf_counter() - start_time
            logger.info(f"Successfully applied {description} in {elapsed:.2f}s.")
            return
        except TRANSIENT_EXCEPTIONS as exc:
            if attempt == max_retries - 1:
                logger.error(f"Failed to apply {description} after {max_retries} attempts. Last error: {exc}")
                raise
            delay = calculate_backoff(attempt, base_delay=base_delay, max_delay=max_delay, jitter=True)
            logger.warning(
                f"Transient connection error while applying {description}: {exc}. "
                f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})..."
            )
            await asyncio.sleep(delay)
        except Exception as exc:
            logger.error(f"Non-transient error applying {description}: {exc}")
            raise


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


async def init_database(with_seeds: bool = True, check_only: bool = False) -> None:
    """Main database initialization routine with verification."""
    logger.info("=" * 70)
    logger.info("Starting Society Database Bootstrapper & Verification")
    logger.info(f"Target DB Host: {settings.async_database_url.split('@')[-1] if '@' in settings.async_database_url else 'localhost'}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Max Retries: {settings.DB_MAX_RETRIES} with Exponential Back-Off")
    logger.info("=" * 70)

    db_dir = Path(__file__).resolve().parent
    schema_path = db_dir / "schema.sql"
    seeds_path = db_dir / "seeds.sql"

    if check_only:
        logger.info("Check-only mode requested. Inspecting database tables and indexes...")
        tables = await verify_tables()
        indexes = await verify_indexes()
        logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
        logger.info(f"Found {len(indexes)} custom indexes: {', '.join(indexes)}")
        return

    # 1. Apply Schema DDL
    schema_sql = read_sql_file(schema_path)
    await execute_sql_script(schema_sql, "Master Schema DDL & Composite Indexes")

    # 2. Optionally Apply Seeds
    if with_seeds:
        if seeds_path.exists():
            seeds_sql = read_sql_file(seeds_path)
            await execute_sql_script(seeds_sql, "Seed Data (Demo Society, Accounts, Roles)")
        else:
            logger.warning(f"Seeds file not found at {seeds_path}, skipping seed phase.")

    # 3. Post-execution verification
    tables = await verify_tables()
    indexes = await verify_indexes()

    logger.info("=" * 70)
    logger.info("Database Bootstrap Complete & Verified!")
    logger.info(f"Total Public Tables Verified ({len(tables)}):")
    for tbl in tables:
        logger.info(f"  • {tbl}")
    logger.info(f"Total Performance Indexes Verified ({len(indexes)}):")
    for idx in indexes:
        logger.info(f"  • {idx}")
    logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Society Database Initialization Runner")
    parser.add_argument("--no-seeds", action="store_true", help="Do not run seeds.sql")
    parser.add_argument("--check-only", action="store_true", help="Only verify existing tables and indexes without running DDL")
    args = parser.parse_args()

    try:
        asyncio.run(init_database(with_seeds=not args.no_seeds, check_only=args.check_only))
    except KeyboardInterrupt:
        logger.warning("Database initialization aborted by user.")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Fatal error during database initialization: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
