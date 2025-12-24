from alembic import context
from sqlalchemy import create_engine, pool
from pathlib import Path
import os
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.db.base import Base
from src.db.user import User
from src.db.google_credentials import GoogleCredentials

config = context.config
target_metadata = Base.metadata


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")

    # Alembic работает ТОЛЬКО с sync драйверами
    return url.replace("+asyncpg", "+psycopg")


def run_migrations_offline():
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
