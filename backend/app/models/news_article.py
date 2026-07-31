"""房产资讯数据模型。"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class NewsArticle(Base):
    """房产资讯表。"""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="资讯标题")
    summary = Column(Text, nullable=True, comment="摘要")
    content = Column(Text, nullable=False, comment="正文内容（HTML）")
    cover_url = Column(Text, nullable=True, comment="封面图")

    category = Column(String(50), nullable=False, index=True, comment="分类标识")
    category_name = Column(String(50), nullable=True, comment="分类名称")
    tags = Column(JSON, nullable=True, comment="标签数组")

    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="作者ID")
    author_name = Column(String(50), nullable=True, comment="作者名称")
    author_avatar = Column(String(500), nullable=True, comment="作者头像")

    is_published = Column(Boolean, default=False, index=True, comment="是否已发布")
    publish_time = Column(DateTime(timezone=True), nullable=True, index=True, comment="发布时间")
    sort_order = Column(Integer, default=0, index=True, comment="排序权重")

    view_count = Column(Integer, default=0, comment="阅读数")
    like_count = Column(Integer, default=0, comment="点赞数")
    collect_count = Column(Integer, default=0, comment="收藏数")
    share_count = Column(Integer, default=0, comment="分享数")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间（软删除）")

    author = relationship("User", foreign_keys=[author_id])
    interactions = relationship("NewsInteraction", back_populates="news", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_news_articles_publish", "is_published", "publish_time", "sort_order"),
    )

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title={self.title})>"
