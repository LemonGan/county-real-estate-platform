"""Create user feedback workflow table.

Revision ID: f7a1c9d4e2b6
Revises: c4e9f6a2d7b1
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "f7a1c9d4e2b6"
down_revision = "c4e9f6a2d7b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=False, server_default="general"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("contact", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="miniprogram"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.Column("handled_by", sa.Integer(), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["handled_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_feedbacks_user_id", "feedbacks", ["user_id"], unique=False)
    op.create_index("ix_feedbacks_status", "feedbacks", ["status"], unique=False)
    op.create_index("ix_feedbacks_created_at", "feedbacks", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_feedbacks_created_at", table_name="feedbacks")
    op.drop_index("ix_feedbacks_status", table_name="feedbacks")
    op.drop_index("ix_feedbacks_user_id", table_name="feedbacks")
    op.drop_table("feedbacks")
