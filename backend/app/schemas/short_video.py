"""
短视频相关Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ShortVideoBase(BaseModel):
    """短视频基础信息"""
    title: str = Field(..., max_length=200, description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")
    video_url: str = Field(..., description="视频URL")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    video_duration: Optional[int] = Field(None, ge=0, description="视频时长（秒）")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小（字节）")
    property_id: Optional[int] = Field(None, description="关联房源ID")
    platform_tags: Optional[List[str]] = Field(None, description="平台标签数组：抖音、快手、小红书等")


class ShortVideoCreate(ShortVideoBase):
    """创建短视频请求"""
    pass


class ShortVideoUpdate(BaseModel):
    """更新短视频请求"""
    title: Optional[str] = Field(None, max_length=200, description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    property_id: Optional[int] = Field(None, description="关联房源ID")
    platform_tags: Optional[List[str]] = Field(None, description="平台标签数组")


class ShortVideoResponse(ShortVideoBase):
    """短视频响应"""
    id: int
    video_no: Optional[str]
    creator_id: int
    is_published: bool
    publish_time: Optional[datetime]
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    favorite_count: int
    review_status: int
    review_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShortVideoListResponse(BaseModel):
    """短视频列表响应"""
    list: List[ShortVideoResponse]
    total: int
    page: int
    page_size: int


class ShortVideoReviewRequest(BaseModel):
    """审核短视频请求"""
    review_status: int = Field(..., ge=0, le=2, description="审核状态：0待审核，1已通过，2已拒绝")
    review_note: Optional[str] = Field(None, description="审核备注")
    
    @field_validator('review_status')
    @classmethod
    def validate_review_status(cls, v: int) -> int:
        """验证审核状态"""
        valid_statuses = {0, 1, 2}
        if v not in valid_statuses:
            raise ValueError(f'无效的审核状态: {v}，应为0-2之间的值')
        return v
