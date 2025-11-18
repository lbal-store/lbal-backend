"""Expand addresses table to support default flag and timestamps

Revision ID: 20241118_expand_addresses
Revises: 
Create Date: 2025-11-18 04:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20241118_expand_addresses"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("addresses")
    op.create_table(
        "addresses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("line1", sa.String(length=255), nullable=False),
        sa.Column("line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=True),
        sa.Column("postal_code", sa.String(length=50), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=False, server_default=sa.text("'MA'")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"])


def downgrade() -> None:
    op.drop_table("addresses")
    table = op.create_table(
        "addresses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("line1", sa.String, nullable=False),
        sa.Column("city", sa.String, nullable=False),
        sa.Column("country", sa.String, nullable=False),
    )
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"])
