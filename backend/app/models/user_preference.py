"""
用户偏好数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserPreference(Base):
    """用户偏好表 - 用于AI推荐算法"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, comment="用户ID")
    
    # 购房预算偏好
    budget_min = Column(Integer, nullable=True, comment="最小预算（万元）")
    budget_max = Column(Integer, nullable=True, comment="最大预算（万元）")
    area_min = Column(Integer, nullable=True, comment="最小面积（㎡）")
    area_max = Column(Integer, nullable=True, comment="最大面积（㎡）")
    preferred_property_types = Column(JSON, nullable=True, comment="偏好户型类型数组")
    preferred_locations = Column(JSON, nullable=True, comment="偏好位置数组")
    has_children = Column(Boolean, nullable=True, comment="是否有孩子（学区需求）")
    
    # 推荐算法权重配置
    price_weight = Column(Numeric(3, 2), default=0.30, comment="价格权重")
    location_weight = Column(Numeric(3, 2), default=0.30, comment="位置权重")
    school_weight = Column(Numeric(3, 2), default=0.20, comment="学区权重")
    transport_weight = Column(Numeric(3, 2), default=0.20, comment="交通权重")
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id})>"
