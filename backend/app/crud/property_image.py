"""
房源图片CRUD操作
"""
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models.property_image import PropertyImage
from app.models.property import Property
from app.utils.upload import delete_uploaded_image_with_thumbnail

logger = logging.getLogger(__name__)


async def get_property_images(
    db: AsyncSession,
    property_id: int
) -> List[PropertyImage]:
    """获取房源的所有图片"""
    result = await db.execute(
        select(PropertyImage)
        .where(PropertyImage.property_id == property_id)
        .order_by(PropertyImage.sort_order, PropertyImage.created_at)
        .options(selectinload(PropertyImage.property))
    )
    return list(result.scalars().all())


async def get_property_image_by_id(
    db: AsyncSession,
    image_id: int
) -> Optional[PropertyImage]:
    """根据ID获取图片"""
    result = await db.execute(
        select(PropertyImage)
        .where(PropertyImage.id == image_id)
        .options(selectinload(PropertyImage.property))
    )
    return result.scalar_one_or_none()


async def create_property_image(
    db: AsyncSession,
    property_id: int,
    image_url: str,
    thumbnail_url: Optional[str] = None,
    image_type: int = 0,
    sort_order: int = 0,
    is_cover: bool = False,
    file_size: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> PropertyImage:
    """创建房源图片记录"""
    # 如果设置为封面，先取消其他封面
    if is_cover:
        existing_covers = await db.execute(
            select(PropertyImage)
            .where(PropertyImage.property_id == property_id)
            .where(PropertyImage.is_cover == True)
        )
        for cover in existing_covers.scalars().all():
            cover.is_cover = False
    
    db_image = PropertyImage(
        property_id=property_id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        image_type=image_type,
        sort_order=sort_order,
        is_cover=is_cover,
        file_size=file_size,
        width=width,
        height=height
    )
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    return db_image


async def delete_property_image(db: AsyncSession, image_id: int) -> bool:
    """删除房源图片（包括文件系统中的文件）"""
    image = await get_property_image_by_id(db, image_id)
    if not image:
        return False
    
    # 保存文件URL用于删除文件
    image_url = image.image_url
    thumbnail_url = image.thumbnail_url
    
    # 删除数据库记录
    await db.delete(image)
    await db.commit()
    
    # 删除文件系统中的文件
    try:
        deleted = await delete_uploaded_image_with_thumbnail(image_url, thumbnail_url)
        if deleted:
            logger.info(f"成功删除图片文件: {image_url}")
        else:
            logger.warning(f"图片文件不存在或删除失败: {image_url}")
    except Exception as e:
        logger.error(f"删除图片文件时出错: {image_url} - {str(e)}")
        # 文件删除失败不影响数据库记录删除，继续执行
    
    return True


async def update_property_image(
    db: AsyncSession,
    image_id: int,
    image_type: Optional[int] = None,
    sort_order: Optional[int] = None,
    is_cover: Optional[bool] = None
) -> Optional[PropertyImage]:
    """更新图片信息"""
    image = await get_property_image_by_id(db, image_id)
    if not image:
        return None
    
    if image_type is not None:
        image.image_type = image_type
    if sort_order is not None:
        image.sort_order = sort_order
    if is_cover is not None:
        # 如果设置为封面，先取消其他封面
        if is_cover:
            existing_covers = await db.execute(
                select(PropertyImage)
                .where(PropertyImage.property_id == image.property_id)
                .where(PropertyImage.id != image_id)
                .where(PropertyImage.is_cover == True)
            )
            for cover in existing_covers.scalars().all():
                cover.is_cover = False
        image.is_cover = is_cover
    
    await db.commit()
    await db.refresh(image)
    return image


async def set_cover_image(db: AsyncSession, property_id: int, image_id: int) -> bool:
    """设置封面图"""
    image = await get_property_image_by_id(db, image_id)
    if not image or image.property_id != property_id:
        return False
    
    # 取消其他封面
    existing_covers = await db.execute(
        select(PropertyImage)
        .where(PropertyImage.property_id == property_id)
        .where(PropertyImage.id != image_id)
        .where(PropertyImage.is_cover == True)
    )
    for cover in existing_covers.scalars().all():
        cover.is_cover = False
    
    # 设置新封面
    image.is_cover = True
    await db.commit()
    return True
