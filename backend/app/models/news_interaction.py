"""房产资讯互动记录。"""
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class NewsInteraction(Base):
    """单个用户对单篇资讯的互动状态。"""
    __tablename__ = "news_interactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    news_id = Column(Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True, comment="资讯ID")

    is_liked = Column(Boolean, default=False, comment="是否点赞")
    is_collected = Column(Boolean, default=False, comment="是否收藏")
    liked_at = Column(DateTime(timezone=True), nullable=True, comment="点赞时间")
    collected_at = Column(DateTime(timezone=True), nullable=True, comment="收藏时间")
    last_viewed_at = Column(DateTime(timezone=True), nullable=True, comment="最近浏览时间")
    view_count = Column(Integer, default=0, comment="浏览次数")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("User")
    news = relationship("NewsArticle", back_populates="interactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='uq_news_interaction_user_news'),
    )

    def __repr__(self):
        return f"<NewsInteraction(user_id={self.user_id}, news_id={self.news_id})>"
