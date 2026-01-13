"""
推荐算法相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class VideoRecommendationResponse(BaseModel):
    """视频推荐响应"""
    id: int
    user_id: int
    video_id: int
    base_score: Optional[Decimal]
    user_preference_score: Optional[Decimal]
    location_score: Optional[Decimal]
    recency_score: Optional[Decimal]
    engagement_score: Optional[Decimal]
    final_score: Decimal
    is_shown: bool
    shown_at: Optional[datetime]
    clicked: bool
    clicked_at: Optional[datetime]
    created_at: datetime
    
    # 关联的视频信息
    video: Optional[dict] = None
    
    class Config:
        from_attributes = True


class VideoRecommendationListResponse(BaseModel):
    """视频推荐列表响应"""
    list: list[VideoRecommendationResponse]
    total: int
    page: int
    page_size: int
