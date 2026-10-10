"""add structured property media and verification evidence

Revision ID: 0022_add_property_media_and_verification_evidence
Revises: 0021_add_property_provenance
"""
from alembic import op
import sqlalchemy as sa


revision = "0022_add_property_media_and_verification_evidence"
down_revision = "0021_add_property_provenance"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "property_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("media_type", sa.String(length=30), nullable=False, server_default="image"),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="OWNER_UPLOADED"),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("license_reference", sa.String(length=500), nullable=True),
        sa.Column("caption", sa.String(length=500), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_property_media_id", "property_media", ["id"])
    op.create_index("ix_property_media_property_id", "property_media", ["property_id"])

    op.create_table(
        "verification_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("verification_id", sa.Integer(), sa.ForeignKey("verification_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(length=100), nullable=False),
        sa.Column("reference", sa.String(length=1000), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_verification_evidence_id", "verification_evidence", ["id"])
    op.create_index("ix_verification_evidence_verification_id", "verification_evidence", ["verification_id"])


def downgrade():
    op.drop_index("ix_verification_evidence_verification_id", table_name="verification_evidence")
    op.drop_index("ix_verification_evidence_id", table_name="verification_evidence")
    op.drop_table("verification_evidence")
    op.drop_index("ix_property_media_property_id", table_name="property_media")
    op.drop_index("ix_property_media_id", table_name="property_media")
    op.drop_table("property_media")
