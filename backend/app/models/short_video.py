"""
短视频内容数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, SmallInteger, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ShortVideo(Base):
    """短视频内容表 - 支持多平台分发"""
    __tablename__ = "short_videos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_no = Column(String(30), unique=True, nullable=True, index=True, comment="视频编号")
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="创建者ID")
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联房源ID")
    
    # 基本信息
    title = Column(String(200), nullable=False, comment="视频标题")
    description = Column(Text, nullable=True, comment="视频描述")
    video_url = Column(Text, nullable=False, comment="视频URL")
    cover_image_url = Column(Text, nullable=True, comment="封面图片URL")
    video_duration = Column(Integer, nullable=True, comment="视频时长（秒）")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    
    # 平台分发
    platform_tags = Column(JSON, nullable=True, comment="平台标签数组：抖音、快手、小红书等")
    is_published = Column(Boolean, default=False, index=True, comment="是否已发布")
    publish_time = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    
    # 统计信息
    view_count = Column(Integer, default=0, comment="播放次数")
    like_count = Column(Integer, default=0, comment="点赞次数")
    comment_count = Column(Integer, default=0, comment="评论次数")
    share_count = Column(Integer, default=0, comment="分享次数")
    favorite_count = Column(Integer, default=0, comment="收藏次数")
    
    # 审核状态
    review_status = Column(SmallInteger, default=0, index=True, comment="审核状态：0待审核，1已通过，2已拒绝")
    review_note = Column(Text, nullable=True, comment="审核备注")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID")
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="审核时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间（软删除）")
    
    # 关系
    creator = relationship("User", foreign_keys=[creator_id], backref="created_videos")
    property = relationship("Property", backref="videos")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    # 索引
    __table_args__ = (
        Index('idx_short_videos_creator_published', 'creator_id', 'is_published', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ShortVideo(id={self.id}, title={self.title}, creator_id={self.creator_id})>"
