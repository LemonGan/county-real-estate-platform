"""
推荐算法API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.recommendation import (
    VideoRecommendationResponse, VideoRecommendationListResponse
)
from app.crud.recommendation import (
    generate_recommendations, get_recommendations,
    mark_recommendation_shown, mark_recommendation_clicked
)
from app.crud.short_video import get_short_video_by_id
from app.schemas.short_video import ShortVideoResponse

router = APIRouter()


@router.post("/generate", summary="生成推荐视频")
async def generate_video_recommendations(
    limit: int = Query(20, ge=1, le=100, description="生成推荐数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    为用户生成视频推荐
    基于用户偏好、行为数据、地理位置等计算推荐得分
    """
    recommendations = await generate_recommendations(db, current_user.id, limit=limit)
    return {
        "message": "推荐生成成功",
        "count": len(recommendations)
    }


@router.get("", response_model=VideoRecommendationListResponse, summary="获取推荐视频列表")
async def get_video_recommendations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    exclude_shown: bool = Query(True, description="是否排除已展示的推荐"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的推荐视频列表
    按推荐得分降序排列
    """
    recommendations, total = await get_recommendations(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        exclude_shown=exclude_shown
    )
    
    # 转换为响应格式，包含视频详情
    recommendation_list = []
    for rec in recommendations:
        rec_dict = {
            "id": rec.id,
            "user_id": rec.user_id,
            "video_id": rec.video_id,
            "base_score": rec.base_score,
            "user_preference_score": rec.user_preference_score,
            "location_score": rec.location_score,
            "recency_score": rec.recency_score,
            "engagement_score": rec.engagement_score,
            "final_score": rec.final_score,
            "is_shown": rec.is_shown,
            "shown_at": rec.shown_at,
            "clicked": rec.clicked,
            "clicked_at": rec.clicked_at,
            "created_at": rec.created_at,
            "video": None
        }
        
        # 包含视频详情
        if rec.video:
            from app.schemas.short_video import ShortVideoResponse
            rec_dict["video"] = ShortVideoResponse.model_validate(rec.video).model_dump()
        
        recommendation_list.append(rec_dict)
    
    return {
        "list": recommendation_list,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{video_id}/shown", status_code=200, summary="标记推荐已展示")
async def mark_video_shown(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记推荐视频已展示给用户"""
    success = await mark_recommendation_shown(db, current_user.id, video_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推荐记录不存在或已标记"
        )
    return {"message": "标记成功"}


@router.post("/{video_id}/clicked", status_code=200, summary="标记推荐已点击")
async def mark_video_clicked(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记推荐视频已被用户点击"""
    success = await mark_recommendation_clicked(db, current_user.id, video_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推荐记录不存在或已标记"
        )
    return {"message": "标记成功"}
