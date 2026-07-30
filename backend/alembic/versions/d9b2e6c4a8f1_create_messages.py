"""Create persistent in-app messages.

Revision ID: d9b2e6c4a8f1
Revises: f7a1c9d4e2b6
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "d9b2e6c4a8f1"
down_revision = "f7a1c9d4e2b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("type", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("related_id", sa.Integer(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_user_id", "messages", ["user_id"], unique=False)
    op.create_index("ix_messages_type", "messages", ["type"], unique=False)
    op.create_index("ix_messages_related_id", "messages", ["related_id"], unique=False)
    op.create_index("ix_messages_is_read", "messages", ["is_read"], unique=False)
    op.create_index("ix_messages_created_at", "messages", ["created_at"], unique=False)
    op.create_index("idx_messages_user_read_created", "messages", ["user_id", "is_read", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_messages_user_read_created", table_name="messages")
    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_is_read", table_name="messages")
    op.drop_index("ix_messages_related_id", table_name="messages")
    op.drop_index("ix_messages_type", table_name="messages")
    op.drop_index("ix_messages_user_id", table_name="messages")
    op.drop_table("messages")
