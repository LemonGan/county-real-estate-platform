"""
推荐算法CRUD操作
"""
from typing import List, Tuple, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload

from app.models.video_recommendation import VideoRecommendation
from app.models.short_video import ShortVideo
from app.models.user_preference import UserPreference
from app.models.property import Property
from app.models.user import User
from app.utils.recommendation import (
    calculate_base_score, calculate_user_preference_score,
    calculate_location_score, calculate_recency_score,
    calculate_engagement_score, calculate_final_score
)
from app.core.cache import cache_service, CacheKeys, CacheTTL


async def generate_recommendations(
    db: AsyncSession,
    user_id: int,
    limit: int = 20
) -> List[VideoRecommendation]:
    """
    为用户生成视频推荐
    计算所有可用视频的推荐得分并保存
    """
    # 获取用户偏好
    preference_result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    user_preference = preference_result.scalar_one_or_none()
    
    # 获取用户信息（用于地理位置匹配）
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    # 获取所有已发布且审核通过的视频
    videos_result = await db.execute(
        select(ShortVideo)
        .where(ShortVideo.is_published == True)
        .where(ShortVideo.review_status == 1)
        .where(ShortVideo.deleted_at.is_(None))
        .options(selectinload(ShortVideo.property))
    )
    videos = videos_result.scalars().all()
    
    recommendations = []
    
    for video in videos:
        # 检查是否已有推荐记录
        existing_result = await db.execute(
            select(VideoRecommendation)
            .where(VideoRecommendation.user_id == user_id)
            .where(VideoRecommendation.video_id == video.id)
        )
        existing = existing_result.scalar_one_or_none()
        
        # 计算各项得分
        base_score = calculate_base_score(video)
        user_pref_score = calculate_user_preference_score(user_preference, video, video.property)
        loc_score = calculate_location_score(user.current_city if user else None, video, video.property)
        recency_score = calculate_recency_score(video)
        engagement_score = calculate_engagement_score(video)
        
        # 计算最终得分
        final_score = calculate_final_score(
            base_score, user_pref_score, loc_score, recency_score, engagement_score
        )
        
        # 创建或更新推荐记录
        if existing:
            existing.base_score = base_score
            existing.user_preference_score = user_pref_score
            existing.location_score = loc_score
            existing.recency_score = recency_score
            existing.engagement_score = engagement_score
            existing.final_score = final_score
            recommendations.append(existing)
        else:
            new_rec = VideoRecommendation(
                user_id=user_id,
                video_id=video.id,
                base_score=base_score,
                user_preference_score=user_pref_score,
                location_score=loc_score,
                recency_score=recency_score,
                engagement_score=engagement_score,
                final_score=final_score
            )
            db.add(new_rec)
            recommendations.append(new_rec)
    
    await db.commit()
    
    # 返回按得分排序的推荐列表
    recommendations.sort(key=lambda x: x.final_score, reverse=True)
    return recommendations[:limit]


async def get_recommendations(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    exclude_shown: bool = True,
    use_cache: bool = True
) -> Tuple[List[VideoRecommendation], int]:
    """
    获取用户的推荐视频列表（支持缓存）
    """
    # 尝试从缓存获取
    if use_cache and page == 1:  # 只缓存第一页
        cache_key = cache_service.generate_cache_key(
            CacheKeys.video_recommendation(user_id),
            page=page,
            page_size=page_size,
            exclude_shown=exclude_shown
        )
        cached = await cache_service.get(cache_key)
        if cached:
            # 返回缓存的结果（简化处理）
            pass  # 暂时跳过，直接查数据库
    
    query = select(VideoRecommendation).where(VideoRecommendation.user_id == user_id)
    
    if exclude_shown:
        query = query.where(VideoRecommendation.is_shown == False)
    
    # 获取总数
    count_query = select(func.count()).select_from(VideoRecommendation).where(VideoRecommendation.user_id == user_id)
    if exclude_shown:
        count_query = count_query.where(VideoRecommendation.is_shown == False)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询，按得分降序
    query = query.order_by(desc(VideoRecommendation.final_score))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(
        selectinload(VideoRecommendation.video).selectinload(ShortVideo.creator),
        selectinload(VideoRecommendation.video).selectinload(ShortVideo.property)
    )
    
    result = await db.execute(query)
    recommendations = result.scalars().all()
    
    # 缓存结果（第一页）
    if use_cache and page == 1:
        cache_key = cache_service.generate_cache_key(
            CacheKeys.video_recommendation(user_id),
            page=page,
            page_size=page_size,
            exclude_shown=exclude_shown
        )
        # 注意：这里简化处理，实际应该序列化recommendations
        # await cache_service.set(cache_key, recommendations_data, CacheTTL.VIDEO_RECOMMENDATION)
    
    return list(recommendations), total


async def mark_recommendation_shown(
    db: AsyncSession,
    user_id: int,
    video_id: int
) -> bool:
    """标记推荐已展示"""
    result = await db.execute(
        select(VideoRecommendation)
        .where(VideoRecommendation.user_id == user_id)
        .where(VideoRecommendation.video_id == video_id)
    )
    rec = result.scalar_one_or_none()
    
    if rec and not rec.is_shown:
        rec.is_shown = True
        rec.shown_at = datetime.now()
        await db.commit()
        return True
    
    return False


async def mark_recommendation_clicked(
    db: AsyncSession,
    user_id: int,
    video_id: int
) -> bool:
    """标记推荐已点击"""
    result = await db.execute(
        select(VideoRecommendation)
        .where(VideoRecommendation.user_id == user_id)
        .where(VideoRecommendation.video_id == video_id)
    )
    rec = result.scalar_one_or_none()
    
    if rec and not rec.clicked:
        rec.clicked = True
        rec.clicked_at = datetime.now()
        await db.commit()
        return True
    
    return False
