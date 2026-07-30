"""Add property review moderation metadata.

Revision ID: a2f9b7c6d3e4
Revises: d9b2e6c4a8f1
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa


revision = "a2f9b7c6d3e4"
down_revision = "d9b2e6c4a8f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("property_reviews", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("property_reviews", sa.Column("reviewed_by", sa.Integer(), nullable=True))
    op.add_column("property_reviews", sa.Column("review_note", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_property_reviews_reviewed_by_users",
        "property_reviews",
        "users",
        ["reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_property_reviews_reviewed_by_users", "property_reviews", type_="foreignkey")
    op.drop_column("property_reviews", "review_note")
    op.drop_column("property_reviews", "reviewed_by")
    op.drop_column("property_reviews", "reviewed_at")
