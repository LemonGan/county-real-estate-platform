"""
房源数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum as SQLEnum, SmallInteger, Numeric, Boolean, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class PropertyStatus(str, enum.Enum):
    """房源状态枚举"""
    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    SOLD = "sold"  # 已售
    OFF_SHELF = "off_shelf"  # 下架


class PropertyType(int, enum.Enum):
    """房产类型枚举"""
    RESIDENTIAL = 1  # 住宅
    SHOP = 2  # 商铺
    OFFICE = 3  # 写字楼
    VILLA = 4  # 别墅


class TransactionType(int, enum.Enum):
    """交易类型枚举"""
    SALE = 1  # 出售
    RENT = 2  # 出租


class Property(Base):
    """房源表 - 包含县域市场特色字段"""
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    property_no = Column(String(20), unique=True, nullable=True, index=True, comment="房源编号")
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="经纪人ID")
    
    # 基本信息
    title = Column(String(200), nullable=False, comment="房源标题")
    description = Column(Text, nullable=True, comment="房源描述")
    property_type = Column(SmallInteger, nullable=False, comment="房产类型：1住宅，2商铺，3写字楼，4别墅")
    transaction_type = Column(SmallInteger, nullable=False, comment="交易类型：1出售，2出租")
    
    # 县域特色 - 四级地理位置
    province = Column(String(50), nullable=False, comment="省份")
    city = Column(String(50), nullable=False, index=True, comment="城市")
    district = Column(String(50), nullable=False, index=True, comment="区/县")
    town = Column(String(50), nullable=True, index=True, comment="镇/街道")
    village = Column(String(50), nullable=True, comment="村/社区")
    detail_address = Column(String(200), nullable=True, comment="详细地址")
    longitude = Column(Numeric(10, 7), nullable=True, comment="经度")
    latitude = Column(Numeric(10, 7), nullable=True, comment="纬度")
    
    # 价格与面积
    total_price = Column(Integer, nullable=True, comment="总价（元）")
    unit_price = Column(Integer, nullable=True, index=True, comment="单价（元/㎡）")
    area = Column(Numeric(6, 2), nullable=False, comment="建筑面积（㎡）")
    
    # 房型结构
    room_count = Column(SmallInteger, nullable=True, comment="室数")
    hall_count = Column(SmallInteger, nullable=True, comment="厅数")
    bathroom_count = Column(SmallInteger, nullable=True, comment="卫数")
    floor_info = Column(String(50), nullable=True, comment="楼层信息")
    total_floors = Column(SmallInteger, nullable=True, comment="总层数")
    build_year = Column(SmallInteger, nullable=True, comment="建成年份")
    decoration_type = Column(SmallInteger, nullable=True, comment="装修类型")
    
    # 县域特色配置
    school_district = Column(String(100), nullable=True, comment="学区信息（返乡用户重点关注）")
    transportation = Column(JSON, nullable=True, comment="交通配套数组")
    surrounding_facilities = Column(JSON, nullable=True, comment="周边设施详情")
    property_rights_years = Column(SmallInteger, nullable=True, comment="产权年限")
    down_payment_ratio = Column(Numeric(3, 1), nullable=True, comment="首付比例")
    
    # 多媒体资源
    cover_image_url = Column(Text, nullable=True, comment="封面图片URL")
    video_urls = Column(JSON, nullable=True, comment="视频链接数组")
    vr_url = Column(Text, nullable=True, comment="VR看房链接")
    has_vr = Column(Boolean, default=False, comment="是否有VR")
    has_video = Column(Boolean, default=False, comment="是否有视频")
    
    # 状态管理
    status = Column(SmallInteger, default=1, index=True, comment="状态：1在售，2已售，3下架")
    audit_status = Column(SmallInteger, default=0, comment="审核状态：0待审核，1已通过，2已拒绝")
    verify_status = Column(Boolean, default=False, comment="真实性验证")
    
    # 营销统计
    view_count = Column(Integer, default=0, comment="浏览次数")
    favorite_count = Column(Integer, default=0, comment="收藏次数")
    inquiry_count = Column(Integer, default=0, comment="咨询次数")
    share_count = Column(Integer, default=0, comment="分享次数")
    
    # SEO与标签
    tags = Column(JSON, nullable=True, comment="标签数组")
    keywords = Column(String(500), nullable=True, comment="关键词")
    
    # 联系信息（兼容旧字段）
    contact_phone = Column(String(20), nullable=True, comment="联系电话")
    contact_name = Column(String(50), nullable=True, comment="联系人姓名")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间（软删除）")
    
    # 关系
    agent = relationship("User", foreign_keys=[agent_id], backref="agent_properties")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    favorites = relationship("PropertyFavorite", back_populates="property", cascade="all, delete-orphan")
    
    # 兼容旧字段名：owner作为agent的别名（使用property装饰器）
    @property
    def owner(self):
        """兼容旧字段名，返回agent"""
        return self.agent
    
    @property
    def owner_id(self):
        """兼容旧字段名，返回agent_id"""
        return self.agent_id
    
    # 复合索引
    __table_args__ = (
        Index('idx_properties_location', 'city', 'district', 'town'),
        Index('idx_properties_price_area', 'total_price', 'area'),
        Index('idx_properties_advanced', 'city', 'district', 'property_type', 'transaction_type', 'total_price', 'area', 'status'),
    )
    
    def __repr__(self):
        return f"<Property(id={self.id}, title={self.title}, total_price={self.total_price})>"
