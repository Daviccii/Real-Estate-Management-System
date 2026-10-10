"""add property provenance and source metadata

Revision ID: 0021_add_property_provenance
Revises: 0020_merge_and_align_building_schema
"""
from alembic import op
import sqlalchemy as sa


revision = "0021_add_property_provenance"
down_revision = "0020_merge_and_align_building_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "property_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="PROP_NOXA_VERIFIED"),
        sa.Column("authorization_status", sa.String(length=50), nullable=False, server_default="approved"),
        sa.Column("terms_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_sync", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_property_sources_id", "property_sources", ["id"])
    for name, column_type in (
        ("source_id", sa.Integer()),
        ("source_type", sa.String(length=50)),
        ("source_name", sa.String(length=255)),
        ("source_reference", sa.String(length=255)),
        ("verification_status", sa.String(length=50)),
        ("last_verified_at", sa.DateTime()),
        ("listing_status", sa.String(length=50)),
        ("is_demo", sa.Boolean()),
    ):
        if name == "source_id":
            column = sa.Column(name, column_type, sa.ForeignKey("property_sources.id", ondelete="SET NULL"), nullable=True)
        else:
            column = sa.Column(name, column_type, nullable=True)
        op.add_column("properties", column)
    op.create_index("ix_properties_source_id", "properties", ["source_id"])
    op.create_index("ix_properties_verification_status", "properties", ["verification_status"])
    op.create_index("ix_properties_listing_status", "properties", ["listing_status"])
    op.create_index("ix_properties_is_demo", "properties", ["is_demo"])


def downgrade():
    for index in ("ix_properties_is_demo", "ix_properties_listing_status", "ix_properties_verification_status", "ix_properties_source_id"):
        op.drop_index(index, table_name="properties")
    for name in ("is_demo", "listing_status", "last_verified_at", "verification_status", "source_reference", "source_name", "source_type", "source_id"):
        op.drop_column("properties", name)
    op.drop_index("ix_property_sources_id", table_name="property_sources")
    op.drop_table("property_sources")
