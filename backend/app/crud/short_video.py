"""
短视频CRUD操作
"""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload

from app.models.short_video import ShortVideo
from app.models.property import Property


async def get_short_video_by_id(db: AsyncSession, video_id: int) -> Optional[ShortVideo]:
    """根据ID获取短视频"""
    result = await db.execute(
        select(ShortVideo)
        .where(ShortVideo.id == video_id)
        .where(ShortVideo.deleted_at.is_(None))
        .options(
            selectinload(ShortVideo.creator),
            selectinload(ShortVideo.property),
            selectinload(ShortVideo.reviewer)
        )
    )
    return result.scalar_one_or_none()


async def get_short_videos(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    creator_id: Optional[int] = None,
    property_id: Optional[int] = None,
    is_published: Optional[bool] = None,
    review_status: Optional[int] = None,
    keyword: Optional[str] = None
) -> Tuple[List[ShortVideo], int]:
    """获取短视频列表"""
    query = select(ShortVideo).where(ShortVideo.deleted_at.is_(None))
    
    # 筛选条件
    if creator_id:
        query = query.where(ShortVideo.creator_id == creator_id)
    if property_id:
        query = query.where(ShortVideo.property_id == property_id)
    if is_published is not None:
        query = query.where(ShortVideo.is_published == is_published)
    if review_status is not None:
        query = query.where(ShortVideo.review_status == review_status)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(
            or_(
                ShortVideo.title.like(keyword_pattern),
                ShortVideo.description.like(keyword_pattern)
            )
        )
    
    # 获取总数
    count_query = select(func.count()).select_from(ShortVideo).where(ShortVideo.deleted_at.is_(None))
    if creator_id:
        count_query = count_query.where(ShortVideo.creator_id == creator_id)
    if property_id:
        count_query = count_query.where(ShortVideo.property_id == property_id)
    if is_published is not None:
        count_query = count_query.where(ShortVideo.is_published == is_published)
    if review_status is not None:
        count_query = count_query.where(ShortVideo.review_status == review_status)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        count_query = count_query.where(
            or_(
                ShortVideo.title.like(keyword_pattern),
                ShortVideo.description.like(keyword_pattern)
            )
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(desc(ShortVideo.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(
        selectinload(ShortVideo.creator),
        selectinload(ShortVideo.property)
    )
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return list(videos), total


async def create_short_video(
    db: AsyncSession,
    creator_id: int,
    video_data: dict
) -> ShortVideo:
    """创建短视频"""
    # 生成视频编号
    video_no = f"VID{uuid.uuid4().hex[:12].upper()}"
    
    db_video = ShortVideo(
        video_no=video_no,
        creator_id=creator_id,
        **video_data
    )
    db.add(db_video)
    await db.commit()
    await db.refresh(db_video)
    return db_video


async def update_short_video(
    db: AsyncSession,
    video_id: int,
    video_data: dict
) -> Optional[ShortVideo]:
    """更新短视频信息"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        return None
    
    for key, value in video_data.items():
        if value is not None:
            setattr(video, key, value)
    
    await db.commit()
    await db.refresh(video)
    return video


async def delete_short_video(db: AsyncSession, video_id: int) -> bool:
    """删除短视频（软删除）"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        return False
    
    from datetime import datetime
    video.deleted_at = datetime.now()
    await db.commit()
    return True


async def publish_short_video(
    db: AsyncSession,
    video_id: int
) -> Optional[ShortVideo]:
    """发布短视频"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        return None
    
    if video.review_status != 1:  # 只有审核通过的才能发布
        return None
    
    from datetime import datetime
    video.is_published = True
    video.publish_time = datetime.now()
    await db.commit()
    await db.refresh(video)
    return video


async def review_short_video(
    db: AsyncSession,
    video_id: int,
    review_status: int,
    reviewer_id: int,
    review_note: Optional[str] = None
) -> Optional[ShortVideo]:
    """审核短视频"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        return None
    
    from datetime import datetime
    video.review_status = review_status
    video.reviewer_id = reviewer_id
    video.review_note = review_note
    video.reviewed_at = datetime.now()
    
    await db.commit()
    await db.refresh(video)
    return video


async def increment_video_stat(
    db: AsyncSession,
    video_id: int,
    stat_type: str  # 'view', 'like', 'comment', 'share', 'favorite'
) -> bool:
    """增加视频统计数据"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        return False
    
    stat_map = {
        'view': 'view_count',
        'like': 'like_count',
        'comment': 'comment_count',
        'share': 'share_count',
        'favorite': 'favorite_count'
    }
    
    if stat_type in stat_map:
        current_value = getattr(video, stat_map[stat_type]) or 0
        setattr(video, stat_map[stat_type], current_value + 1)
        await db.commit()
        return True
    
    return False
