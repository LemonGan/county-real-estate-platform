"""Create news articles and interactions tables.

Revision ID: 9c7d4b1a5e02
Revises: e8b3d5a9c2f4
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa


revision = "9c7d4b1a5e02"
down_revision = "e8b3d5a9c2f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("category_name", sa.String(length=50), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=50), nullable=True),
        sa.Column("author_avatar", sa.String(length=500), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("publish_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("collect_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("share_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_news_articles_category", "news_articles", ["category"], unique=False)
    op.create_index("ix_news_articles_is_published", "news_articles", ["is_published"], unique=False)
    op.create_index("ix_news_articles_publish_time", "news_articles", ["publish_time"], unique=False)
    op.create_index("idx_news_articles_publish", "news_articles", ["is_published", "publish_time", "sort_order"], unique=False)

    op.create_table(
        "news_interactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("news_id", sa.Integer(), nullable=False),
        sa.Column("is_liked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_collected", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("liked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["news_id"], ["news_articles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "news_id", name="uq_news_interaction_user_news"),
    )
    op.create_index("ix_news_interactions_user_id", "news_interactions", ["user_id"], unique=False)
    op.create_index("ix_news_interactions_news_id", "news_interactions", ["news_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_news_interactions_news_id", table_name="news_interactions")
    op.drop_index("ix_news_interactions_user_id", table_name="news_interactions")
    op.drop_table("news_interactions")
    op.drop_index("idx_news_articles_publish", table_name="news_articles")
    op.drop_index("ix_news_articles_publish_time", table_name="news_articles")
    op.drop_index("ix_news_articles_is_published", table_name="news_articles")
    op.drop_index("ix_news_articles_category", table_name="news_articles")
    op.drop_table("news_articles")
