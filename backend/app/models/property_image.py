"""
房源图片数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, SmallInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PropertyImage(Base):
    """房源图片表 - 房源多媒体资源管理"""
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True, comment="房源ID")
    
    image_url = Column(Text, nullable=False, comment="图片URL")
    thumbnail_url = Column(Text, nullable=True, comment="缩略图URL")
    image_type = Column(SmallInteger, default=0, comment="图片类型：0普通，1客厅，2卧室，3厨房，4卫生间，5阳台")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_cover = Column(Boolean, default=False, comment="是否封面图")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    width = Column(Integer, nullable=True, comment="宽度（像素）")
    height = Column(Integer, nullable=True, comment="高度（像素）")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    property = relationship("Property", back_populates="images")
    
    def __repr__(self):
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, image_type={self.image_type})>"
