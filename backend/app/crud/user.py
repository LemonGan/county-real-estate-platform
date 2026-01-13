"""
用户CRUD操作
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    """根据手机号获取用户"""
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """创建新用户"""
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        phone=user_data.phone,
        hashed_password=hashed_password,
        nickname=user_data.nickname,
        avatar=user_data.avatar,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_openid(db: AsyncSession, openid: str) -> Optional[User]:
    """根据微信openid获取用户"""
    result = await db.execute(select(User).where(User.openid == openid))
    return result.scalar_one_or_none()


async def get_user_by_unionid(db: AsyncSession, unionid: str) -> Optional[User]:
    """根据微信unionid获取用户"""
    result = await db.execute(select(User).where(User.unionid == unionid))
    return result.scalar_one_or_none()


async def create_wechat_user(
    db: AsyncSession,
    openid: str,
    session_key: str,
    unionid: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar: Optional[str] = None
) -> User:
    """创建微信用户"""
    # 生成一个临时手机号（微信用户可能没有手机号）
    # 格式：wechat_ + openid前8位 + 随机数字
    import random
    temp_phone = f"wechat_{openid[:8]}{random.randint(1000, 9999)}"
    
    # 确保手机号唯一
    while await get_user_by_phone(db, temp_phone):
        temp_phone = f"wechat_{openid[:8]}{random.randint(1000, 9999)}"
    
    db_user = User(
        openid=openid,
        unionid=unionid,
        session_key=session_key,
        phone=temp_phone,
        nickname=nickname,
        avatar=avatar,
        is_active=True,
        source_channel="wechat_miniprogram"
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_wechat_user_info(
    db: AsyncSession,
    user_id: int,
    session_key: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar: Optional[str] = None
) -> Optional[User]:
    """更新微信用户信息"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    if session_key:
        user.session_key = session_key
    if nickname:
        user.nickname = nickname
    if avatar:
        user.avatar = avatar
    
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: int, user_data: dict) -> Optional[User]:
    """更新用户信息"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    for key, value in user_data.items():
        if value is not None:
            setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user
