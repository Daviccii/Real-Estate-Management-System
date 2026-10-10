"""Add indexes for high-volume lease, unit, payment, and maintenance queries.

Revision ID: 0025_add_scaling_indexes
Revises: 0024_prevent_concurrent_viewing_bookings
"""

from alembic import op


revision = "0025_add_scaling_indexes"
down_revision = "0024_prevent_concurrent_viewing_bookings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_leases_status_end_date",
        "leases",
        ["status", "end_date"],
    )
    op.create_index(
        "ix_units_property_status",
        "units",
        ["property_id", "status"],
    )
    op.create_index(
        "ix_units_status_type_bedrooms",
        "units",
        ["status", "unit_type", "bedrooms"],
    )
    op.create_index(
        "ix_payments_tenant_created",
        "payments",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_maintenance_tenant_created",
        "maintenance",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_maintenance_tenant_created", table_name="maintenance")
    op.drop_index("ix_payments_tenant_created", table_name="payments")
    op.drop_index("ix_units_status_type_bedrooms", table_name="units")
    op.drop_index("ix_units_property_status", table_name="units")
    op.drop_index("ix_leases_status_end_date", table_name="leases")
