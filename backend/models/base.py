"""Declarative base plus the marker that keeps Alembic out of foreign tables."""

from sqlalchemy.orm import DeclarativeBase

#: Tables created and migrated elsewhere -- the ESPN ingest pipeline
#: (EXPERIMENTS/supabase_schema.sql) and Supabase GoTrue. They are mapped so
#: foreign keys and relationships resolve; alembic/env.py filters them out.
EXTERNAL = {"info": {"is_external": True}}


class Base(DeclarativeBase):
    pass
