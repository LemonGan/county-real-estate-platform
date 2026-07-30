"""站内通知数据模型。"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Message(Base):
    """持久化站内通知。"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(SmallInteger, nullable=False, default=1, index=True, comment="1系统通知，2预约提醒，3房源动态")
    related_id = Column(Integer, nullable=True, index=True)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_messages_user_read_created", "user_id", "is_read", "created_at"),
    )
