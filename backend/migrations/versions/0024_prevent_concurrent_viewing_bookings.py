"""Prevent concurrent booking of the same viewing slot.

Revision ID: 0024_prevent_concurrent_viewing_bookings
Revises: 0023_add_owner_expenses_provider_billing
"""

from alembic import op


revision = "0024_prevent_concurrent_viewing_bookings"
down_revision = "0023_add_owner_expenses_provider_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The application conflict check is useful for a fast response, but only
    # a database constraint can close the race between two simultaneous
    # requests.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_viewings_active_property_slot
        ON viewings (property_id, viewing_date, start_time)
        WHERE status IN ('requested', 'pending', 'confirmed')
        """
    )


def downgrade() -> None:
    op.drop_index("uq_viewings_active_property_slot", table_name="viewings")
