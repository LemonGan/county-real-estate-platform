"""Create persistent short-video interactions.

Revision ID: f2a7c9e4b1d8
Revises: d6f4a8c1e2b7
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa


revision = "f2a7c9e4b1d8"
down_revision = "d6f4a8c1e2b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_likes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["short_videos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "video_id", name="uq_video_likes_user_video"),
    )
    op.create_index("ix_video_likes_user_id", "video_likes", ["user_id"], unique=False)
    op.create_index("ix_video_likes_video_id", "video_likes", ["video_id"], unique=False)
    op.create_index("idx_video_likes_video_created", "video_likes", ["video_id", "created_at"], unique=False)

    op.create_table(
        "video_favorites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["short_videos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "video_id", name="uq_video_favorites_user_video"),
    )
    op.create_index("ix_video_favorites_user_id", "video_favorites", ["user_id"], unique=False)
    op.create_index("ix_video_favorites_video_id", "video_favorites", ["video_id"], unique=False)
    op.create_index("idx_video_favorites_video_created", "video_favorites", ["video_id", "created_at"], unique=False)

    op.create_table(
        "video_comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["video_id"], ["short_videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["video_comments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_video_comments_video_id", "video_comments", ["video_id"], unique=False)
    op.create_index("ix_video_comments_user_id", "video_comments", ["user_id"], unique=False)
    op.create_index("ix_video_comments_parent_id", "video_comments", ["parent_id"], unique=False)
    op.create_index("idx_video_comments_video_created", "video_comments", ["video_id", "created_at"], unique=False)

    op.create_table(
        "video_comment_likes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["comment_id"], ["video_comments.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "comment_id", name="uq_video_comment_likes_user_comment"),
    )
    op.create_index("ix_video_comment_likes_user_id", "video_comment_likes", ["user_id"], unique=False)
    op.create_index("ix_video_comment_likes_comment_id", "video_comment_likes", ["comment_id"], unique=False)
    op.create_index("idx_video_comment_likes_comment_created", "video_comment_likes", ["comment_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_video_comment_likes_comment_created", table_name="video_comment_likes")
    op.drop_index("ix_video_comment_likes_comment_id", table_name="video_comment_likes")
    op.drop_index("ix_video_comment_likes_user_id", table_name="video_comment_likes")
    op.drop_table("video_comment_likes")
    op.drop_index("idx_video_comments_video_created", table_name="video_comments")
    op.drop_index("ix_video_comments_parent_id", table_name="video_comments")
    op.drop_index("ix_video_comments_user_id", table_name="video_comments")
    op.drop_index("ix_video_comments_video_id", table_name="video_comments")
    op.drop_table("video_comments")
    op.drop_index("idx_video_favorites_video_created", table_name="video_favorites")
    op.drop_index("ix_video_favorites_video_id", table_name="video_favorites")
    op.drop_index("ix_video_favorites_user_id", table_name="video_favorites")
    op.drop_table("video_favorites")
    op.drop_index("idx_video_likes_video_created", table_name="video_likes")
    op.drop_index("ix_video_likes_video_id", table_name="video_likes")
    op.drop_index("ix_video_likes_user_id", table_name="video_likes")
    op.drop_table("video_likes")
