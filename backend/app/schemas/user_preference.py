"""
用户偏好相关Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class UserPreferenceBase(BaseModel):
    """用户偏好基础信息"""
    budget_min: Optional[int] = Field(None, ge=0, description="最小预算（万元）")
    budget_max: Optional[int] = Field(None, ge=0, description="最大预算（万元）")
    area_min: Optional[int] = Field(None, ge=0, description="最小面积（㎡）")
    area_max: Optional[int] = Field(None, ge=0, description="最大面积（㎡）")
    preferred_property_types: Optional[List[int]] = Field(None, description="偏好户型类型数组：1住宅，2商铺，3写字楼，4别墅")
    preferred_locations: Optional[List[str]] = Field(None, description="偏好位置数组（城市/区县）")
    has_children: Optional[bool] = Field(None, description="是否有孩子（学区需求）")
    
    # 推荐算法权重配置
    price_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="价格权重（0-1）")
    location_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="位置权重（0-1）")
    school_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="学区权重（0-1）")
    transport_weight: Optional[Decimal] = Field(None, ge=0, le=1, description="交通权重（0-1）")
    
    @field_validator('budget_max')
    @classmethod
    def validate_budget_max(cls, v: Optional[int], info) -> Optional[int]:
        """验证最大预算应大于等于最小预算"""
        if v is not None and 'budget_min' in info.data:
            budget_min = info.data.get('budget_min')
            if budget_min is not None and v < budget_min:
                raise ValueError('最大预算应大于等于最小预算')
        return v
    
    @field_validator('area_max')
    @classmethod
    def validate_area_max(cls, v: Optional[int], info) -> Optional[int]:
        """验证最大面积应大于等于最小面积"""
        if v is not None and 'area_min' in info.data:
            area_min = info.data.get('area_min')
            if area_min is not None and v < area_min:
                raise ValueError('最大面积应大于等于最小面积')
        return v
    
    @field_validator('preferred_property_types')
    @classmethod
    def validate_property_types(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """验证户型类型"""
        if v is not None:
            valid_types = {1, 2, 3, 4}  # 1住宅，2商铺，3写字楼，4别墅
            for prop_type in v:
                if prop_type not in valid_types:
                    raise ValueError(f'无效的户型类型: {prop_type}，应为1-4之间的值')
        return v


class UserPreferenceCreate(UserPreferenceBase):
    """创建用户偏好请求"""
    pass


class UserPreferenceUpdate(UserPreferenceBase):
    """更新用户偏好请求"""
    pass


class UserPreferenceResponse(UserPreferenceBase):
    """用户偏好响应"""
    id: int
    user_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True
