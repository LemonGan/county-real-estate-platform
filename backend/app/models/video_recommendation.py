"""
视频推荐算法数据模型
"""
from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class VideoRecommendation(Base):
    """视频推荐算法表 - AI推荐算法计算结果存储"""
    __tablename__ = "video_recommendations"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    video_id = Column(Integer, ForeignKey("short_videos.id", ondelete="CASCADE"), nullable=False, index=True, comment="视频ID")
    
    # 推荐算法权重
    base_score = Column(Numeric(5, 4), nullable=True, comment="基础得分")
    user_preference_score = Column(Numeric(5, 4), nullable=True, comment="用户偏好得分")
    location_score = Column(Numeric(5, 4), nullable=True, comment="地理位置得分")
    recency_score = Column(Numeric(5, 4), nullable=True, comment="时效性得分")
    engagement_score = Column(Numeric(5, 4), nullable=True, comment="互动率得分")
    final_score = Column(Numeric(6, 4), nullable=False, index=True, comment="最终得分")
    
    # 推荐状态追踪
    is_shown = Column(Boolean, default=False, index=True, comment="是否已展示")
    shown_at = Column(DateTime(timezone=True), nullable=True, comment="展示时间")
    clicked = Column(Boolean, default=False, comment="是否已点击")
    clicked_at = Column(DateTime(timezone=True), nullable=True, comment="点击时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User", backref="video_recommendations")
    video = relationship("ShortVideo", backref="recommendations")
    
    # 复合索引
    __table_args__ = (
        Index('idx_video_rec_user_score', 'user_id', 'final_score'),
        Index('idx_video_rec_realtime', 'user_id', 'final_score', 'is_shown'),
    )
    
    def __repr__(self):
        return f"<VideoRecommendation(user_id={self.user_id}, video_id={self.video_id}, final_score={self.final_score})>"
