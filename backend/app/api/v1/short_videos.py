"""
短视频管理API
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.short_video import (
    ShortVideoCreate, ShortVideoUpdate, ShortVideoResponse,
    ShortVideoListResponse, ShortVideoReviewRequest, VideoCommentCreate
)
from app.crud.short_video import (
    get_short_video_by_id, get_short_videos, create_short_video,
    update_short_video, delete_short_video, publish_short_video,
    review_short_video, increment_video_stat
)
from app.crud.video_interaction import (
    create_video_comment, delete_video_comment, get_comment_replies, get_public_video,
    get_video_comment, get_video_comments, get_video_interaction_status,
    toggle_comment_like, toggle_video_favorite, toggle_video_like,
)

router = APIRouter()



@router.post("", response_model=ShortVideoResponse, status_code=201, summary="创建短视频")
async def create_short_video_endpoint(
    video_data: ShortVideoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新的短视频（需要登录）"""
    video = await create_short_video(
        db,
        creator_id=current_user.id,
        video_data=video_data.model_dump(exclude_unset=True)
    )
    return video


@router.get("", response_model=ShortVideoListResponse, summary="获取短视频列表")
async def get_short_videos_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    creator_id: Optional[int] = Query(None, description="创建者ID筛选"),
    property_id: Optional[int] = Query(None, description="关联房源ID筛选"),
    is_published: Optional[bool] = Query(None, description="是否已发布筛选"),
    review_status: Optional[int] = Query(None, ge=0, le=2, description="审核状态筛选：0待审核，1已通过，2已拒绝"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题、描述）"),
    db: AsyncSession = Depends(get_db)
):
    """获取公开短视频列表：仅返回已发布且审核通过的内容。"""
    if is_published not in (None, True) or review_status not in (None, 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="公开列表仅支持查询已发布且审核通过的短视频",
        )
    videos, total = await get_short_videos(
        db,
        page=page,
        page_size=page_size,
        creator_id=creator_id,
        property_id=property_id,
        is_published=True,
        review_status=1,
        keyword=keyword
    )
    return {
        "list": videos,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{video_id}", response_model=ShortVideoResponse, summary="获取短视频详情")
async def get_short_video_detail(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取短视频详细信息"""
    video = await get_short_video_by_id(db, video_id)
    if not video or not video.is_published or video.review_status != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )
    return video


@router.put("/{video_id}", response_model=ShortVideoResponse, summary="更新短视频信息")
async def update_short_video_endpoint(
    video_id: int,
    video_data: ShortVideoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新短视频信息（仅创建者可修改）"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )
    
    # 检查权限：只有创建者可以修改
    if video.creator_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此短视频"
        )
    
    updated_video = await update_short_video(
        db,
        video_id=video_id,
        video_data=video_data.model_dump(exclude_unset=True)
    )
    return updated_video


@router.delete("/{video_id}", status_code=204, summary="删除短视频")
async def delete_short_video_endpoint(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除短视频（软删除，仅创建者可删除）"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )
    
    # 检查权限
    if video.creator_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此短视频"
        )
    
    success = await delete_short_video(db, video_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )
    
    return None


@router.post("/{video_id}/publish", response_model=ShortVideoResponse, summary="发布短视频")
async def publish_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发布短视频（仅创建者可发布，且需审核通过）"""
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )
    
    # 检查权限
    if video.creator_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权发布此短视频"
        )
    
    published_video = await publish_short_video(db, video_id)
    if not published_video:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有审核通过的视频才能发布"
        )
    
    return published_video


@router.post("/{video_id}/review", response_model=ShortVideoResponse, summary="审核短视频")
async def review_video(
    video_id: int,
    review_data: ShortVideoReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """审核短视频（仅管理员可操作）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权审核短视频"
        )
    
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )
    
    reviewed_video = await review_short_video(
        db,
        video_id=video_id,
        review_status=review_data.review_status,
        reviewer_id=current_user.id,
        review_note=review_data.review_note
    )
    return reviewed_video


def _comment_response(comment, current_user_id: Optional[int] = None, is_liked: bool = False):
    user = comment.user
    parent = comment.parent
    parent_user = parent.user if parent and parent.user else None
    return {
        "id": comment.id,
        "video_id": comment.video_id,
        "parent_id": comment.parent_id,
        "content": comment.content,
        "like_count": comment.like_count or 0,
        "status": comment.status,
        "user_id": comment.user_id,
        "user_name": (user.nickname or "用户") if user else "用户",
        "user_avatar": user.avatar if user and user.avatar else "",
        "reply_to_name": (parent_user.nickname or "用户") if parent_user else None,
        "is_liked": is_liked,
        "is_owner": current_user_id == comment.user_id,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


async def _require_public_video(db: AsyncSession, video_id: int):
    video = await get_public_video(db, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="短视频不存在")
    return video


@router.post("/{video_id}/stats/{stat_type}", status_code=200, summary="增加视频统计数据")
async def increment_stat(
    video_id: int,
    stat_type: str = Path(..., regex="^(view|like|comment|share|favorite)$", description="统计类型"),
    db: AsyncSession = Depends(get_db)
):
    """只允许匿名写入播放、分享等非账号归属统计。"""
    if stat_type not in {"view", "share"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该互动请使用专用接口")
    await _require_public_video(db, video_id)
    success = await increment_video_stat(db, video_id, stat_type)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="短视频不存在")
    return {"message": "统计更新成功"}


@router.get("/{video_id}/interaction-status", summary="获取短视频互动状态")
async def get_interaction_status(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _require_public_video(db, video_id)
    return {"video_id": video_id, **(await get_video_interaction_status(db, video_id, current_user.id))}


@router.post("/{video_id}/like/", summary="点赞或取消点赞短视频")
async def like_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await _require_public_video(db, video_id)
    is_liked, like_count = await toggle_video_like(db, video_id, current_user.id)
    return {"video_id": video_id, "is_liked": is_liked, "like_count": like_count}


@router.post("/{video_id}/favorite/", summary="收藏或取消收藏短视频")
async def favorite_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await _require_public_video(db, video_id)
    is_favorited, favorite_count = await toggle_video_favorite(db, video_id, current_user.id)
    return {"video_id": video_id, "is_favorited": is_favorited, "favorite_count": favorite_count}


@router.get("/{video_id}/comments/", summary="获取视频评论列表")
async def get_video_comments_endpoint(
    video_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    await _require_public_video(db, video_id)
    comments, total = await get_video_comments(db, video_id, page, page_size)
    replies = await get_comment_replies(db, [comment.id for comment in comments])
    replies_by_parent = {}
    for reply in replies:
        replies_by_parent.setdefault(reply.parent_id, []).append(_comment_response(reply))
    items = []
    for comment in comments:
        item = _comment_response(comment)
        item["replies"] = replies_by_parent.get(comment.id, [])
        items.append(item)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/{video_id}/comments/", status_code=status.HTTP_201_CREATED, summary="发表视频评论")
async def create_video_comment_endpoint(
    video_id: int,
    comment_data: VideoCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _require_public_video(db, video_id)
    content = comment_data.content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="评论内容不能为空")
    try:
        comment = await create_video_comment(db, video_id, current_user.id, content, comment_data.parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _comment_response(comment, current_user_id=current_user.id)


@router.post("/comments/{comment_id}/like/", summary="点赞或取消点赞评论")
async def like_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    comment = await get_video_comment(db, comment_id)
    if not comment or comment.status != 1 or not await get_public_video(db, comment.video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    is_liked, like_count = await toggle_comment_like(db, comment, current_user.id)
    return {"comment_id": comment_id, "is_liked": is_liked, "like_count": like_count}


@router.delete("/comments/{comment_id}/", status_code=status.HTTP_204_NO_CONTENT, summary="删除视频评论")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    comment = await get_video_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此评论")
    await delete_video_comment(db, comment)
    return None
