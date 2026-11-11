"""Alembic environment.

Only tables this application owns are under Alembic's control. The four ESPN
tables (teams/players/games/appearances) are created and migrated by
EXPERIMENTS/supabase_schema.sql + supabase_sync.py, and auth.users belongs to
Supabase GoTrue -- all five are present in Base.metadata so that foreign keys
and relationships resolve, but `include_object` below keeps autogenerate from
ever emitting DDL against them.

Metadata comes from backend_2.models (the SQL-backed app). The legacy
backend/models.py is left in place but is not the migration source.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Project root on sys.path so `backend` imports work however alembic is invoked.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from backend.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DATABASE_URL is the Postgres connection string (with the database password),
# NOT SUPABASE_SECRET_KEY -- that key only talks to the PostgREST HTTP API.
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Escape % so ConfigParser interpolation does not choke on encoded passwords.
    config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata

# Table names Alembic must never generate DDL for. Derived from the models'
# own `info` markers so adding a new application table needs no change here --
# unmarked tables are managed by default, which is the safe direction to fail.
EXTERNAL_TABLES = {
    table.name
    for table in Base.metadata.tables.values()
    if table.info.get("is_external")
}


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table":
        if name in EXTERNAL_TABLES:
            return False
        # Never manage anything outside `public` (notably the auth schema).
        if getattr(obj, "schema", None) not in (None, "public"):
            return False
    return True


def _require_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if not url or url.startswith("driver://"):
        raise RuntimeError(
            "DATABASE_URL is not set. Add the Supabase Postgres connection string "
            "to .env -- Dashboard -> Project Settings -> Database -> Connection "
            "string (prefer the pooler on port 6543)."
        )
    return url


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting (`alembic upgrade head --sql`)."""
    context.configure(
        url=_require_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _require_url()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
