"""Load Oracle Processor Core Factor Table (070634) reference rows."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_oracle_processor_core_factors"
down_revision: str | None = "0010_host_named_users_required"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace processor core factors with the Oracle 070634 table and re-match profiles."""
    from types import SimpleNamespace

    from license_tracker.db.seed import processor_core_factor_insert_rows
    from license_tracker.domain.license_calc import match_core_factor

    bind = op.get_bind()

    profiles = (
        bind.execute(
            sa.text(
                """
            SELECT id, cpu_model, core_factor, core_factor_id
            FROM host_cpu_profiles
            """
            )
        )
        .mappings()
        .all()
    )

    bind.execute(sa.text("UPDATE host_cpu_profiles SET core_factor_id = NULL"))
    bind.execute(sa.text("DELETE FROM processor_core_factors"))

    core_factor_table = sa.table(
        "processor_core_factors",
        sa.column("id", sa.String(length=36)),
        sa.column("name", sa.String(length=256)),
        sa.column("match_pattern", sa.String(length=256)),
        sa.column("core_factor", sa.Float()),
        sa.column("priority", sa.Integer()),
        sa.column("is_default", sa.Boolean()),
        sa.column("notes", sa.String(length=4000)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    insert_rows = processor_core_factor_insert_rows()
    if insert_rows:
        op.bulk_insert(core_factor_table, insert_rows)

    factor_rows = (
        bind.execute(
            sa.text(
                """
            SELECT id, match_pattern, core_factor, priority, is_default
            FROM processor_core_factors
            """
            )
        )
        .mappings()
        .all()
    )
    factors = [
        SimpleNamespace(
            id=row["id"],
            match_pattern=row["match_pattern"],
            core_factor=row["core_factor"],
            priority=row["priority"],
            is_default=bool(row["is_default"]),
        )
        for row in factor_rows
    ]

    for profile in profiles:
        was_manual_override = (
            profile["core_factor_id"] is None and profile["core_factor"] is not None
        )
        if was_manual_override:
            continue

        matched = match_core_factor(profile["cpu_model"], factors)
        if matched is None:
            bind.execute(
                sa.text(
                    """
                    UPDATE host_cpu_profiles
                    SET core_factor = NULL, core_factor_id = NULL
                    WHERE id = :id
                    """
                ),
                {"id": profile["id"]},
            )
            continue

        bind.execute(
            sa.text(
                """
                UPDATE host_cpu_profiles
                SET core_factor = :core_factor, core_factor_id = :core_factor_id
                WHERE id = :id
                """
            ),
            {
                "id": profile["id"],
                "core_factor": matched.core_factor,
                "core_factor_id": str(matched.id),
            },
        )


def downgrade() -> None:
    """No-op; prior sparse seed rows are not restored."""
