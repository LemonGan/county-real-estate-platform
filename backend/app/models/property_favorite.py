"""
用户收藏房源数据模型
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PropertyFavorite(Base):
    """用户收藏房源表"""
    __tablename__ = "property_favorites"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True, comment="房源ID")
    
    price_alert = Column(Boolean, default=False, comment="价格变动提醒")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='uq_user_property_favorite'),
    )
    
    def __repr__(self):
        return f"<PropertyFavorite(user_id={self.user_id}, property_id={self.property_id})>"
