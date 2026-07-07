"""Add named_users_required for NUP-licensed hosts."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_host_named_users_required"
down_revision: str | None = "0009_host_license_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add hosts.named_users_required."""
    with op.batch_alter_table("hosts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("named_users_required", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Drop hosts.named_users_required."""
    with op.batch_alter_table("hosts", schema=None) as batch_op:
        batch_op.drop_column("named_users_required")
