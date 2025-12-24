"""add server defaults to timestamps

Revision ID: 3d61ddb9659b
Revises: bd57339db21b
Create Date: 2025-12-23 02:59:09.187969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d61ddb9659b'
down_revision: Union[str, Sequence[str], None] = 'bd57339db21b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "users",
        "created_at",
        server_default=sa.func.now(),
    )

    op.alter_column(
        "google_credentials",
        "created_at",
        server_default=sa.func.now(),
    )

    op.alter_column(
        "google_credentials",
        "updated_at",
        server_default=sa.func.now(),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
