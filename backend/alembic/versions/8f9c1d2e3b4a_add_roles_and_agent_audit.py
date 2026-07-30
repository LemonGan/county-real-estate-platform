"""Add roles, agent review workflow and audit logs.

Revision ID: 8f9c1d2e3b4a
Revises: 3ce77a4e1e5a
Create Date: 2026-07-28
"""
from alembic import op
import sqlalchemy as sa

revision = "8f9c1d2e3b4a"
down_revision = "3ce77a4e1e5a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("roles", sa.JSON(), nullable=True, comment="后台角色数组"))
    op.add_column("users", sa.Column("agent_application_status", sa.String(length=20), nullable=False, server_default="none", comment="经纪人申请状态"))
    op.add_column("users", sa.Column("agent_company", sa.String(length=100), nullable=True, comment="经纪人所属公司"))
    op.add_column("users", sa.Column("agent_application_submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("agent_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("agent_reviewed_by", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("agent_review_note", sa.Text(), nullable=True))
    op.create_index("ix_users_agent_application_status", "users", ["agent_application_status"], unique=False)
    op.create_foreign_key("fk_users_agent_reviewed_by", "users", "users", ["agent_reviewed_by"], ["id"], ondelete="SET NULL")
    op.execute("""
        UPDATE users
        SET roles = CASE
            WHEN is_superuser = 1 THEN JSON_ARRAY('superadmin')
            WHEN is_agent = 1 THEN JSON_ARRAY('agent')
            ELSE JSON_ARRAY('user')
        END,
        agent_application_status = CASE
            WHEN is_agent = 1 THEN 'approved'
            ELSE 'none'
        END
        WHERE roles IS NULL
    """)
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_admin_audit_logs_actor_id", "admin_audit_logs", ["actor_id"], unique=False)
    op.create_index("ix_admin_audit_logs_action", "admin_audit_logs", ["action"], unique=False)
    op.create_index("ix_admin_audit_logs_target_id", "admin_audit_logs", ["target_id"], unique=False)
    op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_target_id", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_action", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_actor_id", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    op.drop_constraint("fk_users_agent_reviewed_by", "users", type_="foreignkey")
    op.drop_index("ix_users_agent_application_status", table_name="users")
    for column in ["agent_review_note", "agent_reviewed_by", "agent_reviewed_at", "agent_application_submitted_at", "agent_company", "agent_application_status", "roles"]:
        op.drop_column("users", column)
