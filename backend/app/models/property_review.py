"""
房源评价数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PropertyReview(Base):
    """房源评价表"""
    __tablename__ = "property_reviews"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True, comment="房源ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    
    # 评分 (1-5星)
    rating = Column(Float, nullable=False, default=5.0, comment="评分")
    
    # 评价内容
    content = Column(Text, nullable=True, comment="评价内容")
    
    # 图片
    images = Column(Text, nullable=True, comment="评价图片，逗号分隔")
    
    # 状态
    status = Column(SmallInteger, default=1, comment="状态：0隐藏，1显示")
    
    # 审核
    is_verified = Column(SmallInteger, default=0, comment="是否审核通过：0待审核，1通过，2拒绝")
    
    # 时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    property = relationship("Property", back_populates="reviews")
    user = relationship("User")
    
    def __repr__(self):
        return f"<PropertyReview(id={self.id}, property_id={self.property_id}, rating={self.rating})>"
