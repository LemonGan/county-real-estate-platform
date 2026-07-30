"""Add message related type.

Revision ID: c4d8e1f2a6b9
Revises: a2f9b7c6d3e4
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa


revision = "c4d8e1f2a6b9"
down_revision = "a2f9b7c6d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("related_type", sa.String(length=30), nullable=True))
    op.create_index("ix_messages_related_type", "messages", ["related_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_messages_related_type", table_name="messages")
    op.drop_column("messages", "related_type")
