"""
房源图片相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PropertyImageBase(BaseModel):
    """房源图片基础信息"""
    image_type: int = Field(0, ge=0, le=5, description="图片类型：0普通，1客厅，2卧室，3厨房，4卫生间，5阳台")
    sort_order: int = Field(0, description="排序顺序")
    is_cover: bool = Field(False, description="是否封面图")


class PropertyImageCreate(PropertyImageBase):
    """创建房源图片请求"""
    pass


class PropertyImageUpdate(BaseModel):
    """更新房源图片请求"""
    image_type: Optional[int] = Field(None, ge=0, le=5)
    sort_order: Optional[int] = None
    is_cover: Optional[bool] = None


class PropertyImageResponse(PropertyImageBase):
    """房源图片响应"""
    id: int
    property_id: int
    image_url: str
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PropertyImageListResponse(BaseModel):
    """房源图片列表响应"""
    list: list[PropertyImageResponse]
    total: int
