"""Add companies, user membership, and invitations.

Revision ID: 0027_companies_and_invitations
Revises: 0026_create_background_jobs
"""

from alembic import op
import sqlalchemy as sa


revision = "0027_companies_and_invitations"
down_revision = "0026_create_background_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_companies_slug", "companies", ["slug"], unique=True)
    op.create_index("ix_companies_is_active", "companies", ["is_active"])
    op.create_table(
        "company_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_company_invitations_lookup", "company_invitations", ["company_id", "email", "accepted_at"])
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_users_company_id", "companies", ["company_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_users_company_id", "users", ["company_id"])
    with op.batch_alter_table("properties") as batch:
        batch.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_properties_company_id", "companies", ["company_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_properties_company_id", "properties", ["company_id"])
    op.execute("INSERT INTO companies (name, slug, is_active, created_at, updated_at) VALUES ('Legacy Organization', 'legacy-organization', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
    op.execute("UPDATE users SET company_id = (SELECT id FROM companies WHERE slug = 'legacy-organization') WHERE company_id IS NULL")
    op.execute("UPDATE properties SET company_id = (SELECT u.company_id FROM users u WHERE u.id = properties.owner_id) WHERE company_id IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("properties") as batch:
        batch.drop_constraint("fk_properties_company_id", type_="foreignkey")
        batch.drop_column("company_id")
    op.drop_index("ix_users_company_id", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_company_id", type_="foreignkey")
        batch.drop_column("company_id")
    op.drop_index("ix_company_invitations_lookup", table_name="company_invitations")
    op.drop_table("company_invitations")
    op.drop_index("ix_companies_is_active", table_name="companies")
    op.drop_index("ix_companies_slug", table_name="companies")
    op.drop_table("companies")
