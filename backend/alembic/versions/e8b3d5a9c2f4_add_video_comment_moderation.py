"""Add moderation metadata to short-video comments.

Revision ID: e8b3d5a9c2f4
Revises: f2a7c9e4b1d8
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa


revision = "e8b3d5a9c2f4"
down_revision = "f2a7c9e4b1d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("video_comments", sa.Column("status", sa.SmallInteger(), nullable=False, server_default="0"))
    op.add_column("video_comments", sa.Column("reviewed_by", sa.Integer(), nullable=True))
    op.add_column("video_comments", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("video_comments", sa.Column("review_note", sa.Text(), nullable=True))
    op.create_foreign_key("fk_video_comments_reviewed_by", "video_comments", "users", ["reviewed_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_video_comments_status", "video_comments", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_video_comments_status", table_name="video_comments")
    op.drop_constraint("fk_video_comments_reviewed_by", "video_comments", type_="foreignkey")
    op.drop_column("video_comments", "review_note")
    op.drop_column("video_comments", "reviewed_at")
    op.drop_column("video_comments", "reviewed_by")
    op.drop_column("video_comments", "status")
