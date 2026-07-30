"""Add property review metadata and protect public listing visibility.

Revision ID: c4e9f6a2d7b1
Revises: 8f9c1d2e3b4a
Create Date: 2026-07-29
"""
from alembic import op
import sqlalchemy as sa

revision = "c4e9f6a2d7b1"
down_revision = "8f9c1d2e3b4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("audit_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("properties", sa.Column("audit_reviewed_by", sa.Integer(), nullable=True))
    op.add_column("properties", sa.Column("audit_review_note", sa.Text(), nullable=True))
    op.create_index("ix_properties_audit_status", "properties", ["audit_status"], unique=False)
    op.create_foreign_key(
        "fk_properties_audit_reviewed_by",
        "properties",
        "users",
        ["audit_reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )
    # Existing in-sale listings predate this workflow; preserve their visibility.
    op.execute(
        "UPDATE properties SET audit_status = 1 "
        "WHERE audit_status = 0 AND status = 1 AND deleted_at IS NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_properties_audit_reviewed_by", "properties", type_="foreignkey")
    op.drop_index("ix_properties_audit_status", table_name="properties")
    op.drop_column("properties", "audit_review_note")
    op.drop_column("properties", "audit_reviewed_by")
    op.drop_column("properties", "audit_reviewed_at")
