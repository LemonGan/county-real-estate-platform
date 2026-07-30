"""房源收藏 CRUD。"""
from typing import Optional, Tuple, List

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.models.property_favorite import PropertyFavorite


async def get_favorite_by_id(
    db: AsyncSession, favorite_id: int, user_id: Optional[int] = None
) -> Optional[PropertyFavorite]:
    conditions = [PropertyFavorite.id == favorite_id]
    if user_id is not None:
        conditions.append(PropertyFavorite.user_id == user_id)
    result = await db.execute(
        select(PropertyFavorite)
        .join(PropertyFavorite.property)
        .where(
            *conditions,
            Property.deleted_at.is_(None),
            Property.audit_status == 1,
        )
        .options(
            selectinload(PropertyFavorite.property).selectinload(Property.images),
            selectinload(PropertyFavorite.property).selectinload(Property.agent),
        )
    )
    return result.scalar_one_or_none()


async def get_favorites(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
) -> Tuple[List[PropertyFavorite], int]:
    """获取用户可见的收藏列表；已删除、未审核房源不会继续展示。"""
    conditions = [
        PropertyFavorite.user_id == user_id,
        Property.deleted_at.is_(None),
        Property.audit_status == 1,
    ]
    total = (await db.execute(
        select(func.count()).select_from(PropertyFavorite)
        .join(PropertyFavorite.property)
        .where(*conditions)
    )).scalar() or 0
    result = await db.execute(
        select(PropertyFavorite)
        .join(PropertyFavorite.property)
        .where(*conditions)
        .order_by(PropertyFavorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(
            selectinload(PropertyFavorite.property).selectinload(Property.images),
            selectinload(PropertyFavorite.property).selectinload(Property.agent),
        )
    )
    return list(result.scalars().all()), total


async def check_favorite(db: AsyncSession, user_id: int, property_id: int) -> bool:
    result = await db.execute(
        select(PropertyFavorite.id).where(
            PropertyFavorite.user_id == user_id,
            PropertyFavorite.property_id == property_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def create_favorite(db: AsyncSession, user_id: int, property_id: int) -> PropertyFavorite:
    """收藏一套已审核、在售房源，并原子增加收藏计数。"""
    property_obj = (await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.deleted_at.is_(None),
            Property.audit_status == 1,
            Property.status == 1,
        )
    )).scalar_one_or_none()
    if not property_obj:
        raise ValueError("房源不存在、未审核通过或当前不可收藏")

    favorite = PropertyFavorite(user_id=user_id, property_id=property_id)
    db.add(favorite)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("该房源已被收藏") from exc

    await db.execute(
        update(Property)
        .where(Property.id == property_id)
        .values(favorite_count=func.coalesce(Property.favorite_count, 0) + 1)
    )
    await db.commit()
    result = await get_favorite_by_id(db, favorite.id, user_id)
    if not result:
        raise RuntimeError("收藏创建后无法读取")
    return result


async def delete_favorite(db: AsyncSession, user_id: int, property_id: int) -> bool:
    result = await db.execute(
        select(PropertyFavorite).where(
            PropertyFavorite.user_id == user_id,
            PropertyFavorite.property_id == property_id,
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        return False
    await db.delete(favorite)
    await db.execute(
        update(Property)
        .where(Property.id == property_id)
        .values(favorite_count=func.greatest(func.coalesce(Property.favorite_count, 0) - 1, 0))
    )
    await db.commit()
    return True


async def delete_favorite_by_id(db: AsyncSession, user_id: int, favorite_id: int) -> bool:
    favorite = (await db.execute(
        select(PropertyFavorite).where(
            PropertyFavorite.id == favorite_id,
            PropertyFavorite.user_id == user_id,
        )
    )).scalar_one_or_none()
    if not favorite:
        return False
    return await delete_favorite(db, user_id, favorite.property_id)
