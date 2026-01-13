"""
用户行为相关Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class UserBehaviorCreate(BaseModel):
    """创建用户行为请求"""
    behavior_type: int = Field(..., ge=1, le=5, description="行为类型：1浏览，2收藏，3分享，4电话咨询，5看房预约")
    target_type: int = Field(..., ge=1, le=3, description="目标类型：1房源，2视频，3文章")
    target_id: int = Field(..., ge=1, description="目标ID")
    duration: Optional[int] = Field(None, ge=0, description="停留时长（秒）")
    action_data: Optional[Dict[str, Any]] = Field(None, description="详细行为数据（JSON）")
    
    @field_validator('behavior_type')
    @classmethod
    def validate_behavior_type(cls, v: int) -> int:
        """验证行为类型"""
        valid_types = {1, 2, 3, 4, 5}
        if v not in valid_types:
            raise ValueError(f'无效的行为类型: {v}，应为1-5之间的值')
        return v
    
    @field_validator('target_type')
    @classmethod
    def validate_target_type(cls, v: int) -> int:
        """验证目标类型"""
        valid_types = {1, 2, 3}
        if v not in valid_types:
            raise ValueError(f'无效的目标类型: {v}，应为1-3之间的值')
        return v


class UserBehaviorResponse(BaseModel):
    """用户行为响应"""
    id: int
    user_id: int
    behavior_type: int
    target_type: int
    target_id: int
    duration: Optional[int]
    action_data: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserBehaviorListResponse(BaseModel):
    """用户行为列表响应"""
    list: list[UserBehaviorResponse]
    total: int
    page: int
    page_size: int


class UserBehaviorStatsResponse(BaseModel):
    """用户行为统计响应"""
    behavior_type: Dict[str, int]
    target_type: Dict[str, int]
    total_duration: int
    days: int
