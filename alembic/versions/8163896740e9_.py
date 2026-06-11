"""empty message

Revision ID: 8163896740e9
Revises: 0d044786eb72
Create Date: 2026-06-10 08:22:17.754707

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8163896740e9"
down_revision: Union[str, Sequence[str], None] = "0d044786eb72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Rename the column using op.alter_column
    op.alter_column("tenant", "api_key", new_column_name="api_key_hash")

    # 2. Rename the existing unique index to match the new column name
    op.execute("ALTER INDEX ix_tenant_api_key RENAME TO ix_tenant_api_key_hash")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Revert the unique index name
    op.execute("ALTER INDEX ix_tenant_api_key_hash RENAME TO ix_tenant_api_key")

    # 2. Revert the column name back
    op.alter_column("tenant", "api_key_hash", new_column_name="api_key")
