"""Global application settings and configuration loader."""
import os
from pathlib import Path

# Load .env file with python-dotenv or fallback parser
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

# Database Provider Selection: "postgres" (Local / Direct Postgres) or "supabase" (Cloud Supabase)
# If DB_PROVIDER is not set, auto-detect: if SUPABASE_URL exists -> supabase, else -> postgres
_explicit_provider = os.getenv("DB_PROVIDER")
if _explicit_provider:
    DB_PROVIDER = _explicit_provider.lower().strip()
else:
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"):
        DB_PROVIDER = "supabase"
    else:
        DB_PROVIDER = "postgres"

# PostgreSQL Connection URL (Local or Cloud direct connection)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)

# Supabase Credentials (Cloud PostgREST API)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Task Queue & Ingestion Settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 900))  # 15 minutes default
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
