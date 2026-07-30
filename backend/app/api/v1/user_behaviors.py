"""
用户行为管理API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.property import Property
from app.models.user import User
from app.models.user_behavior import UserBehavior
from app.schemas.user_behavior import (
    UserBehaviorCreate, UserBehaviorResponse, UserBehaviorListResponse,
    UserBehaviorStatsResponse
)
from app.crud.user_behavior import (
    create_user_behavior, get_user_behaviors, get_user_behavior_stats
)

router = APIRouter()


@router.post("/behaviors", response_model=UserBehaviorResponse, status_code=201, summary="记录用户行为")
async def record_user_behavior(
    behavior_data: UserBehaviorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """记录用户行为（浏览、收藏、分享等）"""
    behavior = await create_user_behavior(
        db,
        user_id=current_user.id,
        behavior_type=behavior_data.behavior_type,
        target_type=behavior_data.target_type,
        target_id=behavior_data.target_id,
        duration=behavior_data.duration,
        action_data=behavior_data.action_data
    )
    return behavior


@router.get("/behaviors", response_model=UserBehaviorListResponse, summary="获取用户行为列表")
async def get_my_behaviors(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    behavior_type: Optional[int] = Query(None, ge=1, le=5, description="行为类型筛选：1浏览，2收藏，3分享，4电话咨询，5看房预约"),
    target_type: Optional[int] = Query(None, ge=1, le=3, description="目标类型筛选：1房源，2视频，3文章"),
    days: Optional[int] = Query(None, ge=1, description="查询最近N天的记录"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的行为记录列表"""
    behaviors, total = await get_user_behaviors(
        db,
        user_id=current_user.id,
        behavior_type=behavior_type,
        target_type=target_type,
        page=page,
        page_size=page_size,
        days=days
    )
    return {
        "list": behaviors,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/behaviors/stats", response_model=UserBehaviorStatsResponse, summary="获取用户行为统计")
async def get_my_behavior_stats(
    days: int = Query(30, ge=1, le=365, description="统计最近N天的数据"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的行为统计数据"""
    stats = await get_user_behavior_stats(db, current_user.id, days=days)
    return stats

@router.get("/history/properties", summary="获取当前用户的房源浏览历史")
async def get_property_browsing_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """仅返回当前仍公开可见的房源摘要，不暴露已下线或未审核内容。"""
    conditions = (
        UserBehavior.user_id == current_user.id,
        UserBehavior.behavior_type == 1,
        UserBehavior.target_type == 1,
        Property.deleted_at.is_(None),
        Property.audit_status == 1,
    )
    total = (await db.execute(
        select(func.count(UserBehavior.id))
        .select_from(UserBehavior)
        .join(Property, Property.id == UserBehavior.target_id)
        .where(*conditions)
    )).scalar() or 0
    rows = (await db.execute(
        select(UserBehavior, Property)
        .join(Property, Property.id == UserBehavior.target_id)
        .where(*conditions)
        .order_by(UserBehavior.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all()
    items = []
    for behavior, property_item in rows:
        items.append({
            "id": behavior.id,
            "property_id": property_item.id,
            "viewed_at": behavior.created_at,
            "property": {
                "id": property_item.id,
                "title": property_item.title,
                "total_price": property_item.total_price,
                "area": property_item.area,
                "room_count": property_item.room_count,
                "hall_count": property_item.hall_count,
                "district": property_item.district,
                "detail_address": property_item.detail_address,
                "cover_url": property_item.cover_url or property_item.cover_image_url or "",
                "status": property_item.status,
            },
        })
    return {"list": items, "total": total, "page": page, "page_size": page_size}
