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
    ShortVideoListResponse, ShortVideoReviewRequest
)
from app.crud.short_video import (
    get_short_video_by_id, get_short_videos, create_short_video,
    update_short_video, delete_short_video, publish_short_video,
    review_short_video, increment_video_stat
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
    """获取短视频列表（支持筛选和搜索）"""
    videos, total = await get_short_videos(
        db,
        page=page,
        page_size=page_size,
        creator_id=creator_id,
        property_id=property_id,
        is_published=is_published,
        review_status=review_status,
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
    if not video:
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


@router.post("/{video_id}/stats/{stat_type}", status_code=200, summary="增加视频统计数据")
async def increment_stat(
    video_id: int,
    stat_type: str = Path(..., regex="^(view|like|comment|share|favorite)$", description="统计类型"),
    db: AsyncSession = Depends(get_db)
):
    """增加视频统计数据（播放、点赞、评论、分享、收藏）"""
    success = await increment_video_stat(db, video_id, stat_type)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )

    return {"message": "统计更新成功"}


@router.post("/{video_id}/like/", summary="点赞短视频")
async def like_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """点赞/取消点赞短视频"""
    # 检查视频是否存在
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )

    # TODO: 实现点赞/取消点赞逻辑（需要user_video_likes表）
    # 这里暂时只增加统计
    await increment_video_stat(db, video_id, "like")

    return {"liked": True, "like_count": video.like_count + 1}


@router.post("/{video_id}/favorite/", summary="收藏短视频")
async def favorite_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """收藏/取消收藏短视频"""
    # 检查视频是否存在
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )

    # TODO: 实现收藏/取消收藏逻辑（需要user_video_favorites表）
    # 这里暂时只增加统计
    await increment_video_stat(db, video_id, "favorite")

    return {"favorited": True, "favorite_count": video.favorite_count + 1}


@router.get("/{video_id}/comments/", summary="获取视频评论列表")
async def get_video_comments(
    video_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取短视频评论列表"""
    # 检查视频是否存在
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )

    # TODO: 实现评论查询逻辑（需要video_comments表）
    # 这里暂时返回空列表
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size
    }


@router.post("/{video_id}/comments/", status_code=201, summary="发表视频评论")
async def create_video_comment(
    video_id: int,
    comment_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发表短视频评论"""
    # 检查视频是否存在
    video = await get_short_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="短视频不存在"
        )

    # TODO: 实现评论创建逻辑（需要video_comments表）
    # 这里暂时返回模拟数据
    return {
        "id": 1,
        "video_id": video_id,
        "user_id": current_user.id,
        "user_name": current_user.nickname or current_user.phone,
        "user_avatar": current_user.avatar_url,
        "content": comment_data.get("content", ""),
        "parent_id": comment_data.get("parent_id"),
        "like_count": 0,
        "is_liked": False,
        "is_owner": True,
        "created_at": "刚刚"
    }


@router.post("/comments/{comment_id}/like/", summary="点赞评论")
async def like_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """点赞/取消点赞评论"""
    # TODO: 实现评论点赞逻辑（需要comment_likes表）
    return {"liked": True}


@router.delete("/comments/{comment_id}/", status_code=204, summary="删除评论")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除评论（仅评论者可删除）"""
    # TODO: 实现评论删除逻辑
    return None
