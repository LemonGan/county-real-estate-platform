"""
收藏CRUD操作
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.models.property_favorite import PropertyFavorite
from app.models.property import Property


async def get_favorite_by_id(db: AsyncSession, favorite_id: int) -> Optional[PropertyFavorite]:
    """根据ID获取收藏"""
    result = await db.execute(
        select(PropertyFavorite)
        .where(PropertyFavorite.id == favorite_id)
        .options(
            selectinload(PropertyFavorite.property),
            selectinload(PropertyFavorite.user)
        )
    )
    return result.scalar_one_or_none()


async def get_favorites(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10
) -> Tuple[List[PropertyFavorite], int]:
    """获取用户收藏列表（分页）"""
    # 构建查询
    query = select(PropertyFavorite).where(PropertyFavorite.user_id == user_id)
    
    # 获取总数
    count_query = select(func.count()).select_from(PropertyFavorite).where(
        PropertyFavorite.user_id == user_id
    )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(desc(PropertyFavorite.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(
        selectinload(PropertyFavorite.property).selectinload(Property.agent),
        selectinload(PropertyFavorite.user)
    )
    
    result = await db.execute(query)
    favorites = result.scalars().all()
    
    return list(favorites), total


async def check_favorite(db: AsyncSession, user_id: int, property_id: int) -> bool:
    """检查用户是否已收藏该房源"""
    result = await db.execute(
        select(PropertyFavorite).where(
            PropertyFavorite.user_id == user_id,
            PropertyFavorite.property_id == property_id
        )
    )
    return result.scalar_one_or_none() is not None


async def create_favorite(
    db: AsyncSession,
    user_id: int,
    property_id: int
) -> PropertyFavorite:
    """创建收藏"""
    # 检查是否已收藏
    existing = await check_favorite(db, user_id, property_id)
    if existing:
        raise ValueError("该房源已被收藏")
    
    # 检查房源是否存在
    property_result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = property_result.scalar_one_or_none()
    if not property_obj:
        raise ValueError("房源不存在")
    
    db_favorite = PropertyFavorite(
        user_id=user_id,
        property_id=property_id
    )
    db.add(db_favorite)
    
    # 更新房源的收藏数
    property_obj.favorite_count = (property_obj.favorite_count or 0) + 1
    
    await db.commit()
    await db.refresh(db_favorite)
    return db_favorite


async def delete_favorite(db: AsyncSession, user_id: int, property_id: int) -> bool:
    """取消收藏"""
    result = await db.execute(
        select(PropertyFavorite).where(
            PropertyFavorite.user_id == user_id,
            PropertyFavorite.property_id == property_id
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        return False
    
    # 更新房源的收藏数
    property_result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = property_result.scalar_one_or_none()
    if property_obj:
        property_obj.favorite_count = max(0, (property_obj.favorite_count or 0) - 1)
    
    await db.delete(favorite)
    await db.commit()
    return True
