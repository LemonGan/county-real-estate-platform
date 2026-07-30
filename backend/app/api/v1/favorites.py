"""房源收藏 API。"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.crud.favorite import (
    check_favorite,
    create_favorite,
    delete_favorite,
    delete_favorite_by_id,
    get_favorites,
)
from app.models.user import User
from app.schemas.favorite import FavoriteListResponse, FavoriteResponse

router = APIRouter()


class FavoriteCreateRequest(BaseModel):
    property_id: int = Field(gt=0)


async def create_favorite_response(db: AsyncSession, user_id: int, property_id: int):
    try:
        return await create_favorite(db, user_id, property_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/properties/{property_id}", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED, summary="收藏房源")
async def add_favorite(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await create_favorite_response(db, current_user.id, property_id)


@router.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT, summary="取消收藏")
async def remove_favorite(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await delete_favorite(db, current_user.id, property_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该收藏记录")


@router.get("/properties/{property_id}/status", summary="检查收藏状态")
async def check_favorite_status(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return {"is_favorited": await check_favorite(db, current_user.id, property_id), "property_id": property_id}


@router.get("", response_model=FavoriteListResponse, summary="获取收藏列表")
async def get_favorites_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    favorites, total = await get_favorites(db, user_id=current_user.id, page=page, page_size=page_size)
    return {"list": favorites, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED, summary="收藏房源（兼容格式）")
async def add_favorite_compatible(
    favorite_data: FavoriteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await create_favorite_response(db, current_user.id, favorite_data.property_id)


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT, summary="取消收藏（按收藏记录）")
async def remove_favorite_compatible(
    favorite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await delete_favorite_by_id(db, current_user.id, favorite_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该收藏记录")
