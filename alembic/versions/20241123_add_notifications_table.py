"""Add notifications table and unread flag on users

Revision ID: 20241123_add_notifications
Revises: 20241118_expand_addresses
Create Date: 2025-11-23 00:45:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20241123_add_notifications"
down_revision = "20241118_expand_addresses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "has_unread_notifications",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    notification_event_enum = sa.Enum(
        "order_confirmed",
        "order_shipped",
        "order_delivered",
        "item_sold",
        "withdrawal_created",
        "buyer_question",
        "dispute_opened",
        name="notificationevent",
    )
    notification_event_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notifications",
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
        sa.Column("event", notification_event_enum, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    op.alter_column("users", "has_unread_notifications", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("users", "has_unread_notifications")
    sa.Enum(name="notificationevent").drop(op.get_bind(), checkfirst=True)
