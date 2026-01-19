"""
收藏相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.property import PropertyResponse


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: int
    user_id: int
    property_id: int
    price_alert: Optional[bool] = None
    created_at: datetime
    property: PropertyResponse

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    list: list[FavoriteResponse]
    total: int
    page: int
    page_size: int
