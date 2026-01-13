"""
用户偏好管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.user_preference import (
    UserPreferenceCreate, UserPreferenceUpdate, UserPreferenceResponse
)
from app.crud.user_preference import (
    get_user_preference, create_user_preference, update_user_preference,
    delete_user_preference
)

router = APIRouter()


@router.get("/me/preferences", response_model=UserPreferenceResponse, summary="获取当前用户偏好")
async def get_my_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的偏好设置"""
    preference = await get_user_preference(db, current_user.id)
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户偏好不存在，请先创建偏好设置"
        )
    return preference


@router.post("/me/preferences", response_model=UserPreferenceResponse, status_code=201, summary="创建用户偏好")
async def create_my_preferences(
    preference_data: UserPreferenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建当前用户的偏好设置"""
    try:
        preference = await create_user_preference(
            db,
            user_id=current_user.id,
            preference_data=preference_data.model_dump(exclude_unset=True)
        )
        return preference
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me/preferences", response_model=UserPreferenceResponse, summary="更新用户偏好")
async def update_my_preferences(
    preference_data: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新当前用户的偏好设置（如果不存在则创建）"""
    preference = await update_user_preference(
        db,
        user_id=current_user.id,
        preference_data=preference_data.model_dump(exclude_unset=True)
    )
    return preference


@router.patch("/me/preferences", response_model=UserPreferenceResponse, summary="部分更新用户偏好")
async def patch_my_preferences(
    preference_data: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """部分更新当前用户的偏好设置"""
    preference = await update_user_preference(
        db,
        user_id=current_user.id,
        preference_data=preference_data.model_dump(exclude_unset=True)
    )
    return preference


@router.delete("/me/preferences", status_code=204, summary="删除用户偏好")
async def delete_my_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除当前用户的偏好设置"""
    success = await delete_user_preference(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户偏好不存在"
        )
    return None
