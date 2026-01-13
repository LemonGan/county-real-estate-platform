"""
用户偏好CRUD操作
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user_preference import UserPreference
from app.models.user import User


async def get_user_preference(db: AsyncSession, user_id: int) -> Optional[UserPreference]:
    """获取用户偏好"""
    result = await db.execute(
        select(UserPreference)
        .where(UserPreference.user_id == user_id)
        .options(selectinload(UserPreference.user))
    )
    return result.scalar_one_or_none()


async def create_user_preference(
    db: AsyncSession,
    user_id: int,
    preference_data: dict
) -> UserPreference:
    """创建用户偏好"""
    # 检查是否已存在
    existing = await get_user_preference(db, user_id)
    if existing:
        raise ValueError("用户偏好已存在，请使用更新接口")
    
    db_preference = UserPreference(
        user_id=user_id,
        **preference_data
    )
    db.add(db_preference)
    await db.commit()
    await db.refresh(db_preference)
    return db_preference


async def update_user_preference(
    db: AsyncSession,
    user_id: int,
    preference_data: dict
) -> Optional[UserPreference]:
    """更新用户偏好"""
    preference = await get_user_preference(db, user_id)
    if not preference:
        # 如果不存在，创建新的
        return await create_user_preference(db, user_id, preference_data)
    
    # 更新字段
    for key, value in preference_data.items():
        if value is not None:
            setattr(preference, key, value)
    
    await db.commit()
    await db.refresh(preference)
    return preference


async def delete_user_preference(db: AsyncSession, user_id: int) -> bool:
    """删除用户偏好"""
    preference = await get_user_preference(db, user_id)
    if not preference:
        return False
    
    await db.delete(preference)
    await db.commit()
    return True
