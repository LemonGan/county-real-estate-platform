"""
用户行为数据模型
"""
from sqlalchemy import Column, Integer, BigInteger, SmallInteger, DateTime, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserBehavior(Base):
    """用户行为轨迹表 - 短视频推荐和AI算法关键数据源"""
    __tablename__ = "user_behaviors"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    
    # 行为类型：1浏览，2收藏，3分享，4电话咨询，5看房预约
    behavior_type = Column(SmallInteger, nullable=False, comment="行为类型")
    
    # 目标类型：1房源，2视频，3文章
    target_type = Column(SmallInteger, nullable=False, comment="目标类型")
    target_id = Column(Integer, nullable=False, comment="目标ID")
    
    duration = Column(Integer, nullable=True, comment="停留时长（秒）")
    action_data = Column(JSON, nullable=True, comment="详细行为数据")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="behaviors")
    
    # 复合索引
    __table_args__ = (
        Index('idx_user_behaviors_user_target', 'user_id', 'target_type', 'target_id'),
        Index('idx_user_behaviors_type', 'user_id', 'behavior_type', 'target_type'),
    )
    
    def __repr__(self):
        return f"<UserBehavior(user_id={self.user_id}, behavior_type={self.behavior_type}, target_id={self.target_id})>"
