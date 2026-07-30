"""短视频互动的持久化操作。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.short_video import ShortVideo
from app.models.video_interaction import VideoComment, VideoCommentLike, VideoFavorite, VideoLike


async def get_public_video(db: AsyncSession, video_id: int) -> Optional[ShortVideo]:
    result = await db.execute(
        select(ShortVideo).where(
            ShortVideo.id == video_id,
            ShortVideo.deleted_at.is_(None),
            ShortVideo.is_published.is_(True),
            ShortVideo.review_status == 1,
        )
    )
    return result.scalar_one_or_none()


async def _toggle_relation(db: AsyncSession, model, video_id: int, user_id: int, counter: str) -> tuple[bool, int]:
    """切换点赞或收藏，并同步维护短视频统计字段。"""
    relation = (await db.execute(
        select(model).where(model.video_id == video_id, model.user_id == user_id)
    )).scalar_one_or_none()
    if relation:
        await db.delete(relation)
        following = False
        delta = -1
    else:
        db.add(model(video_id=video_id, user_id=user_id))
        following = True
        delta = 1
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        # 并发重复点击最终按“已存在”返回，避免把计数加两次。
        return True, (await get_public_video(db, video_id)).__getattribute__(counter) or 0
    await db.execute(
        update(ShortVideo)
        .where(ShortVideo.id == video_id)
        .values(**{counter: func.greatest(func.coalesce(getattr(ShortVideo, counter), 0) + delta, 0)})
    )
    await db.commit()
    video = await get_public_video(db, video_id)
    return following, getattr(video, counter) or 0


async def toggle_video_like(db: AsyncSession, video_id: int, user_id: int) -> tuple[bool, int]:
    return await _toggle_relation(db, VideoLike, video_id, user_id, "like_count")


async def toggle_video_favorite(db: AsyncSession, video_id: int, user_id: int) -> tuple[bool, int]:
    return await _toggle_relation(db, VideoFavorite, video_id, user_id, "favorite_count")


async def get_video_interaction_status(db: AsyncSession, video_id: int, user_id: int) -> dict:
    is_liked = (await db.execute(
        select(VideoLike.id).where(VideoLike.video_id == video_id, VideoLike.user_id == user_id)
    )).scalar_one_or_none() is not None
    is_favorited = (await db.execute(
        select(VideoFavorite.id).where(VideoFavorite.video_id == video_id, VideoFavorite.user_id == user_id)
    )).scalar_one_or_none() is not None
    return {"is_liked": is_liked, "is_favorited": is_favorited}


async def create_video_comment(
    db: AsyncSession, video_id: int, user_id: int, content: str, parent_id: Optional[int]
) -> VideoComment:
    if parent_id is not None:
        parent = (await db.execute(
            select(VideoComment).where(
                VideoComment.id == parent_id,
                VideoComment.video_id == video_id,
                VideoComment.deleted_at.is_(None),
            )
        )).scalar_one_or_none()
        if not parent:
            raise ValueError("回复的评论不存在或已删除")
    comment = VideoComment(video_id=video_id, user_id=user_id, parent_id=parent_id, content=content)
    db.add(comment)
    await db.flush()
    await db.commit()
    return await get_video_comment(db, comment.id)


async def get_video_comment(db: AsyncSession, comment_id: int) -> Optional[VideoComment]:
    result = await db.execute(
        select(VideoComment).where(
            VideoComment.id == comment_id,
            VideoComment.deleted_at.is_(None),
        ).options(
            selectinload(VideoComment.user),
            selectinload(VideoComment.parent).selectinload(VideoComment.user),
        )
    )
    return result.scalar_one_or_none()


async def get_video_comments(
    db: AsyncSession, video_id: int, page: int, page_size: int
) -> tuple[list[VideoComment], int]:
    conditions = [
        VideoComment.video_id == video_id,
        VideoComment.parent_id.is_(None),
        VideoComment.status == 1,
        VideoComment.deleted_at.is_(None),
    ]
    total = (await db.execute(
        select(func.count()).select_from(VideoComment).where(*conditions)
    )).scalar() or 0
    result = await db.execute(
        select(VideoComment).where(*conditions).order_by(VideoComment.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
        .options(selectinload(VideoComment.user))
    )
    return list(result.scalars().all()), total


async def get_comment_replies(db: AsyncSession, parent_ids: list[int]) -> list[VideoComment]:
    if not parent_ids:
        return []
    result = await db.execute(
        select(VideoComment).where(
            VideoComment.parent_id.in_(parent_ids),
            VideoComment.status == 1,
            VideoComment.deleted_at.is_(None),
        ).order_by(VideoComment.created_at.asc()).options(
            selectinload(VideoComment.user),
            selectinload(VideoComment.parent).selectinload(VideoComment.user),
        )
    )
    return list(result.scalars().all())


async def delete_video_comment(db: AsyncSession, comment: VideoComment) -> bool:
    if comment.deleted_at is not None:
        return False
    comment.deleted_at = datetime.now()
    if comment.status == 1:
        await db.execute(
            update(ShortVideo).where(ShortVideo.id == comment.video_id).values(
                comment_count=func.greatest(func.coalesce(ShortVideo.comment_count, 0) - 1, 0)
            )
        )
    await db.commit()
    return True


async def toggle_comment_like(db: AsyncSession, comment: VideoComment, user_id: int) -> tuple[bool, int]:
    relation = (await db.execute(
        select(VideoCommentLike).where(
            VideoCommentLike.comment_id == comment.id,
            VideoCommentLike.user_id == user_id,
        )
    )).scalar_one_or_none()
    if relation:
        await db.delete(relation)
        liked, delta = False, -1
    else:
        db.add(VideoCommentLike(comment_id=comment.id, user_id=user_id))
        liked, delta = True, 1
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return True, (await get_video_comment(db, comment.id)).like_count or 0
    await db.execute(
        update(VideoComment).where(VideoComment.id == comment.id).values(
            like_count=func.greatest(func.coalesce(VideoComment.like_count, 0) + delta, 0)
        )
    )
    await db.commit()
    fresh = await get_video_comment(db, comment.id)
    return liked, fresh.like_count or 0


async def is_comment_liked(db: AsyncSession, comment_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(VideoCommentLike.id).where(
            VideoCommentLike.comment_id == comment_id,
            VideoCommentLike.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None
