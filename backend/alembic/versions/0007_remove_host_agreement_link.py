"""Remove direct host-to-CSI agreement link."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_remove_host_agreement_link"
down_revision: str | None = "0006_host_entitlements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop hosts.agreement_id; licenses are pooled and assigned per host."""
    with op.batch_alter_table("hosts", schema=None) as batch_op:
        batch_op.drop_constraint("fk_hosts_agreement_id", type_="foreignkey")
        batch_op.drop_index("ix_hosts_agreement_id")
        batch_op.drop_column("agreement_id")


def downgrade() -> None:
    """Restore hosts.agreement_id foreign key."""
    with op.batch_alter_table("hosts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("agreement_id", sa.String(length=36), nullable=True))
        batch_op.create_index("ix_hosts_agreement_id", ["agreement_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_hosts_agreement_id",
            "license_agreements",
            ["agreement_id"],
            ["id"],
            ondelete="SET NULL",
        )
