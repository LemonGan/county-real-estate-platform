"""
房源相关Schema
"""
from pydantic import BaseModel, Field, computed_field, model_validator
from typing import Optional, List, Any
from datetime import datetime
from app.models.property import PropertyStatus


class PropertyImage(BaseModel):
    """房源图片Schema"""
    id: int
    url: str = Field(alias="image_url")
    thumbnail_url: Optional[str] = None
    is_cover: bool = False
    sort_order: int = 0

    class Config:
        from_attributes = True
        populate_by_name = True


class PropertyBase(BaseModel):
    """房源基础信息"""
    title: Optional[str] = Field(None, min_length=2, max_length=200, description="房源标题")
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
    # 经纬度（地图功能需要）
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")
    distance: Optional[float] = Field(None, description="距离当前位置（米）")
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
    # VR和视频
    vr_url: Optional[str] = Field(None, max_length=500, description="VR全景链接")
    video_urls: Optional[List[str]] = Field(None, description="视频链接列表")


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
    from pydantic import model_validator
    
    @model_validator(mode='before')
    @classmethod
    def serialize_images(cls, data):
        if hasattr(data, '__dict__'):
            result = {'id': data.id, 'agent_id': data.agent_id, 'status': data.status}
            for field in ['view_count', 'favorite_count', 'inquiry_count', 'share_count', 'cover_url', 'created_at', 'updated_at', 'title', 'description', 'total_price', 'unit_price', 'area', 'province', 'city', 'district', 'town', 'detail_address', 'longitude', 'latitude', 'property_type', 'transaction_type', 'room_count', 'hall_count', 'bathroom_count', 'floor_info', 'community', 'room_type', 'floor', 'orientation', 'decoration', 'contact_phone', 'contact_name', 'vr_url', 'video_urls', 'has_vr', 'has_video']:
                if hasattr(data, field):
                    result[field] = getattr(data, field)
            if hasattr(data, 'images') and data.images:
                result['images'] = [img.image_url for img in data.images]
            return result
        return data
    
    id: int
    agent_id: int  # 经纪人ID
    status: int  # 使用int类型，因为数据库中是SmallInteger
    view_count: Optional[int] = 0
    favorite_count: Optional[int] = 0
    inquiry_count: Optional[int] = 0
    share_count: Optional[int] = 0
    images: Optional[List[str]] = Field(default=None)  # 房源图片列表
    cover_url: Optional[str] = None  # 封面图片URL
    vr_url: Optional[str] = None  # VR全景链接
    video_urls: Optional[List[str]] = None  # 视频链接列表
    has_vr: Optional[bool] = False  # 是否有VR
    has_video: Optional[bool] = False  # 是否有视频
    created_at: datetime
    updated_at: datetime
    # 覆盖Base中的字段，改为Optional
    area: Optional[float] = None  # 面积改为可选

    @computed_field
    @property
    def owner_id(self) -> int:
        """兼容旧字段名，返回agent_id"""
        return self.agent_id

    @computed_field
    @property
    def rooms(self) -> Optional[int]:
        """兼容旧字段名，返回room_count"""
        return self.room_count

    @computed_field
    @property
    def halls(self) -> Optional[int]:
        """兼容旧字段名，返回hall_count"""
        return self.hall_count

    @model_validator(mode='wrap')
    @classmethod
    def set_price_field(cls, data: Any, handler) -> Any:
        """设置price字段为total_price的值"""
        # 先让Pydantic处理数据
        result = handler(data)
        # 如果是ORM对象转换来的，设置price=total_price
        if isinstance(result, PropertyResponse):
            if result.total_price is not None:
                # 使用object.__setattr__来绕过Pydantic的冻结检查
                object.__setattr__(result, 'price', result.total_price)
        return result

    class Config:
        from_attributes = True
        populate_by_name = True


class PropertyListResponse(BaseModel):
    """房源列表响应"""
    list: list[PropertyResponse]
    total: int
    page: int
    page_size: int
