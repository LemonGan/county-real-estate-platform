"""Create agent follows.

Revision ID: d6f4a8c1e2b7
Revises: c4d8e1f2a6b9
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa


revision = "d6f4a8c1e2b7"
down_revision = "c4d8e1f2a6b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_follows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "agent_id", name="uq_agent_follows_user_agent"),
    )
    op.create_index("ix_agent_follows_user_id", "agent_follows", ["user_id"], unique=False)
    op.create_index("ix_agent_follows_agent_id", "agent_follows", ["agent_id"], unique=False)
    op.create_index("ix_agent_follows_created_at", "agent_follows", ["created_at"], unique=False)
    op.create_index("idx_agent_follows_agent_created", "agent_follows", ["agent_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_agent_follows_agent_created", table_name="agent_follows")
    op.drop_index("ix_agent_follows_created_at", table_name="agent_follows")
    op.drop_index("ix_agent_follows_agent_id", table_name="agent_follows")
    op.drop_index("ix_agent_follows_user_id", table_name="agent_follows")
    op.drop_table("agent_follows")
