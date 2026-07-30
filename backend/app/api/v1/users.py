"""
用户管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.crud.user import get_user_by_id, update_user

router = APIRouter()


def can_view_full_user_profile(requested_user_id: int, current_user: User) -> bool:
    """完整用户资料仅供本人和服务器维护的超级管理员读取。"""
    return current_user.id == requested_user_id or current_user.is_superuser


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前登录用户的详细信息"""
    return current_user


@router.put("/me", response_model=UserResponse, summary="修改当前用户信息")
async def update_current_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """修改当前登录用户的信息"""
    updated_user = await update_user(
        db,
        user_id=current_user.id,
        user_data=user_data.model_dump(exclude_unset=True)
    )
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return updated_user


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户信息")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据 ID 获取完整用户资料（仅本人或超级管理员）。"""
    if not can_view_full_user_profile(user_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看其他用户的完整资料")
    user = await get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user
