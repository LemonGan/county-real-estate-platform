"""
收藏管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.favorite import FavoriteResponse, FavoriteListResponse
from app.crud.favorite import (
    get_favorites, create_favorite, delete_favorite, check_favorite
)

router = APIRouter()


@router.post("/properties/{property_id}", response_model=FavoriteResponse, status_code=201, summary="收藏房源")
async def add_favorite(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """收藏房源"""
    try:
        favorite = await create_favorite(db, current_user.id, property_id)
        return favorite
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/properties/{property_id}", status_code=204, summary="取消收藏")
async def remove_favorite(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """取消收藏房源"""
    success = await delete_favorite(db, current_user.id, property_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该收藏记录"
        )
    return None


@router.get("/properties/{property_id}/status", summary="检查收藏状态")
async def check_favorite_status(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """检查当前用户是否已收藏该房源"""
    is_favorited = await check_favorite(db, current_user.id, property_id)
    return {"is_favorited": is_favorited, "property_id": property_id}


@router.get("", response_model=FavoriteListResponse, summary="获取收藏列表")
async def get_favorites_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的收藏列表"""
    favorites, total = await get_favorites(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    return {
        "list": favorites,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# 兼容前端API格式的端点
@router.post("", response_model=FavoriteResponse, status_code=201, summary="收藏房源（兼容格式）")
async def add_favorite_compatible(
    favorite_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """收藏房源（前端兼容格式，接受body中的property_id）"""
    property_id = favorite_data.get("property_id")
    if not property_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少property_id参数"
        )

    try:
        favorite = await create_favorite(db, current_user.id, property_id)
        return favorite
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{favorite_id}", status_code=204, summary="取消收藏（兼容格式）")
async def remove_favorite_compatible(
    favorite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """取消收藏房源（使用收藏ID，前端兼容格式）"""
    # TODO: 实现通过收藏ID删除的逻辑
    # 当前CRUD通过user_id和property_id删除，需要添加通过favorite_id删除的方法
    success = await delete_favorite_by_id(db, favorite_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该收藏记录"
        )
    return None


async def delete_favorite_by_id(db: AsyncSession, favorite_id: int, user_id: int) -> bool:
    """通过收藏ID删除收藏记录（兼容函数）"""
    # TODO: 实现通过ID删除的逻辑
    # 暂时调用现有的delete_favorite
    from sqlalchemy import select
    from app.models.favorite import Favorite

    result = await db.execute(
        select(Favorite).where(
            Favorite.id == favorite_id,
            Favorite.user_id == user_id
        )
    )
    favorite = result.scalar_one_or_none()

    if favorite:
        return await delete_favorite(db, user_id, favorite.property_id)
    return False
