"""用户关注经纪人关系。"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class AgentFollow(Base):
    __tablename__ = "agent_follows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "agent_id", name="uq_agent_follows_user_agent"),
        Index("idx_agent_follows_agent_created", "agent_id", "created_at"),
    )
