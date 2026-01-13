"""
用户行为CRUD操作
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.models.user_behavior import UserBehavior


async def create_user_behavior(
    db: AsyncSession,
    user_id: int,
    behavior_type: int,
    target_type: int,
    target_id: int,
    duration: Optional[int] = None,
    action_data: Optional[dict] = None
) -> UserBehavior:
    """创建用户行为记录"""
    db_behavior = UserBehavior(
        user_id=user_id,
        behavior_type=behavior_type,
        target_type=target_type,
        target_id=target_id,
        duration=duration,
        action_data=action_data
    )
    db.add(db_behavior)
    await db.commit()
    await db.refresh(db_behavior)
    return db_behavior


async def get_user_behaviors(
    db: AsyncSession,
    user_id: int,
    behavior_type: Optional[int] = None,
    target_type: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    days: Optional[int] = None
) -> Tuple[List[UserBehavior], int]:
    """获取用户行为记录列表"""
    query = select(UserBehavior).where(UserBehavior.user_id == user_id)
    
    # 筛选条件
    if behavior_type is not None:
        query = query.where(UserBehavior.behavior_type == behavior_type)
    if target_type is not None:
        query = query.where(UserBehavior.target_type == target_type)
    if days is not None:
        start_date = datetime.now() - timedelta(days=days)
        query = query.where(UserBehavior.created_at >= start_date)
    
    # 获取总数
    count_query = select(func.count()).select_from(UserBehavior).where(UserBehavior.user_id == user_id)
    if behavior_type is not None:
        count_query = count_query.where(UserBehavior.behavior_type == behavior_type)
    if target_type is not None:
        count_query = count_query.where(UserBehavior.target_type == target_type)
    if days is not None:
        start_date = datetime.now() - timedelta(days=days)
        count_query = count_query.where(UserBehavior.created_at >= start_date)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(desc(UserBehavior.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(selectinload(UserBehavior.user))
    
    result = await db.execute(query)
    behaviors = result.scalars().all()
    
    return list(behaviors), total


async def get_user_behavior_stats(
    db: AsyncSession,
    user_id: int,
    days: int = 30
) -> dict:
    """获取用户行为统计"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 按行为类型统计
    type_result = await db.execute(
        select(
            UserBehavior.behavior_type,
            func.count(UserBehavior.id).label('count')
        )
        .where(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date
            )
        )
        .group_by(UserBehavior.behavior_type)
    )
    behavior_stats = {row.behavior_type: row.count for row in type_result.all()}
    
    # 按目标类型统计
    target_result = await db.execute(
        select(
            UserBehavior.target_type,
            func.count(UserBehavior.id).label('count')
        )
        .where(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date
            )
        )
        .group_by(UserBehavior.target_type)
    )
    target_stats = {row.target_type: row.count for row in target_result.all()}
    
    # 总浏览时长
    duration_result = await db.execute(
        select(func.sum(UserBehavior.duration))
        .where(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date,
                UserBehavior.duration.isnot(None)
            )
        )
    )
    total_duration = duration_result.scalar() or 0
    
    return {
        "behavior_type": {
            "view": behavior_stats.get(1, 0),      # 浏览
            "favorite": behavior_stats.get(2, 0),  # 收藏
            "share": behavior_stats.get(3, 0),     # 分享
            "inquiry": behavior_stats.get(4, 0),   # 电话咨询
            "appointment": behavior_stats.get(5, 0) # 看房预约
        },
        "target_type": {
            "property": target_stats.get(1, 0),    # 房源
            "video": target_stats.get(2, 0),       # 视频
            "article": target_stats.get(3, 0)      # 文章
        },
        "total_duration": int(total_duration),
        "days": days
    }
