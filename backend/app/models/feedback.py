"""用户反馈数据模型。"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(30), nullable=False, server_default="general", comment="反馈分类")
    content = Column(Text, nullable=False, comment="反馈内容")
    contact = Column(String(100), nullable=True, comment="用户自愿留下的联系方式")
    source = Column(String(30), nullable=False, server_default="miniprogram", comment="提交来源")
    status = Column(String(20), nullable=False, server_default="pending", index=True, comment="处理状态")
    admin_response = Column(Text, nullable=True, comment="处理回复")
    handled_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    handled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
