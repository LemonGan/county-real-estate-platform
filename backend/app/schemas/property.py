"""
房源相关Schema
"""
from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime
from app.models.property import PropertyStatus


class PropertyBase(BaseModel):
    """房源基础信息"""
    title: str = Field(..., min_length=2, max_length=200, description="房源标题")
    description: Optional[str] = Field(None, description="房源描述")
    # 兼容字段：price映射到total_price
    price: Optional[float] = Field(None, gt=0, description="价格（元）- 兼容字段，实际使用total_price")
    total_price: Optional[int] = Field(None, gt=0, description="总价（元）")
    unit_price: Optional[int] = Field(None, gt=0, description="单价（元/㎡）")
    area: float = Field(..., gt=0, description="面积（平方米）")
    # 地址相关
    address: Optional[str] = Field(None, max_length=500, description="地址（兼容字段）")
    province: Optional[str] = Field(None, max_length=50, description="省份")
    city: Optional[str] = Field(None, max_length=50, description="城市")
    district: Optional[str] = Field(None, max_length=50, description="区县")
    town: Optional[str] = Field(None, max_length=50, description="镇/街道")
    detail_address: Optional[str] = Field(None, max_length=200, description="详细地址")
    # 房型信息
    property_type: Optional[int] = Field(None, description="房产类型：1住宅，2商铺，3写字楼，4别墅")
    transaction_type: Optional[int] = Field(None, description="交易类型：1出售，2出租")
    room_count: Optional[int] = Field(None, description="室数")
    hall_count: Optional[int] = Field(None, description="厅数")
    bathroom_count: Optional[int] = Field(None, description="卫数")
    floor_info: Optional[str] = Field(None, max_length=50, description="楼层信息")
    # 兼容旧字段
    community: Optional[str] = Field(None, max_length=100, description="小区名称（兼容字段）")
    room_type: Optional[str] = Field(None, max_length=20, description="户型（兼容字段）")
    floor: Optional[str] = Field(None, max_length=20, description="楼层（兼容字段）")
    orientation: Optional[str] = Field(None, max_length=20, description="朝向")
    decoration: Optional[str] = Field(None, max_length=20, description="装修情况")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_name: Optional[str] = Field(None, max_length=50, description="联系人姓名")


class PropertyCreate(PropertyBase):
    """创建房源请求"""
    from pydantic import model_validator
    
    @model_validator(mode='after')
    def map_price_to_total_price(self):
        """将price字段映射到total_price（如果提供了price但没有total_price）"""
        if self.price is not None and self.total_price is None:
            self.total_price = int(self.price)
            self.price = None
        elif self.price is not None and self.total_price is not None:
            # 如果两者都存在，优先使用total_price，忽略price
            self.price = None
        return self


class PropertyUpdate(BaseModel):
    """更新房源请求"""
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    total_price: Optional[int] = Field(None, gt=0, description="总价（元）")
    unit_price: Optional[int] = Field(None, gt=0, description="单价（元/㎡）")
    area: Optional[float] = Field(None, gt=0)
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    town: Optional[str] = Field(None, max_length=50)
    detail_address: Optional[str] = Field(None, max_length=200)
    property_type: Optional[int] = Field(None, description="房产类型：1住宅，2商铺，3写字楼，4别墅")
    transaction_type: Optional[int] = Field(None, description="交易类型：1出售，2出租")
    room_count: Optional[int] = None
    hall_count: Optional[int] = None
    bathroom_count: Optional[int] = None
    floor_info: Optional[str] = Field(None, max_length=50)
    status: Optional[int] = Field(None, ge=1, le=3, description="状态：1在售，2已售，3下架")


class PropertyResponse(PropertyBase):
    """房源响应"""
    id: int
    agent_id: int  # 经纪人ID
    status: int  # 使用int类型，因为数据库中是SmallInteger
    view_count: int
    favorite_count: int
    inquiry_count: int = 0
    share_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def owner_id(self) -> int:
        """兼容旧字段名，返回agent_id"""
        return self.agent_id
    
    class Config:
        from_attributes = True
        populate_by_name = True


class PropertyListResponse(BaseModel):
    """房源列表响应"""
    list: list[PropertyResponse]
    total: int
    page: int
    page_size: int
