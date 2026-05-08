"""
房源CRUD操作
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
import math

from app.models.property import Property
from app.schemas.property import PropertyCreate
from app.core.cache import cache_service, CacheKeys, CacheTTL


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用Haversine公式计算两个经纬度点之间的距离（米）

    Args:
        lat1, lon1: 第一个点的纬度和经度
        lat2, lon2: 第二个点的纬度和经度

    Returns:
        距离（米）
    """
    # 将角度转换为弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine公式
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dlon / 2) ** 2)

    c = 2 * math.asin(math.sqrt(a))

    # 地球半径（米）
    earth_radius = 6371000

    return earth_radius * c


async def get_property_by_id(db: AsyncSession, property_id: int, use_cache: bool = True) -> Optional[Property]:
    """根据ID获取房源（排除已删除的）"""
    # 尝试从缓存获取
    if use_cache:
        cache_key = CacheKeys.property_detail(property_id)
        cached = await cache_service.get(cache_key)
        if cached:
            # 从缓存恢复对象（简化处理，实际可能需要更复杂的序列化）
            pass  # 暂时跳过，直接查数据库

    result = await db.execute(
        select(Property)
        .where(Property.id == property_id)
        .where(Property.deleted_at.is_(None))
        .options(selectinload(Property.agent), selectinload(Property.images))
    )
    property = result.scalar_one_or_none()

    # 缓存结果（转换为可序列化的字典）
    if property and use_cache:
        cache_key = CacheKeys.property_detail(property_id)
        # 注意：这里简化处理，实际应该序列化Property对象
        # await cache_service.set(cache_key, property_dict, CacheTTL.PROPERTY_DETAIL)

    return property


async def get_properties(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    city: Optional[str] = None,
    district: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    rooms: Optional[int] = None,
    property_type: Optional[int] = None,
    transaction_type: Optional[int] = None,
    status: Optional[int] = None,
    keyword: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    max_distance: Optional[int] = None
) -> Tuple[List[Property], int]:
    """获取房源列表（分页和筛选）"""

    def _apply_filters(q):
        """应用筛选条件到查询"""
        q = q.where(Property.deleted_at.is_(None))
        if city:
            q = q.where(Property.city == city)
        if district:
            q = q.where(Property.district == district)
        if min_price is not None:
            q = q.where(Property.total_price >= min_price)
        if max_price is not None:
            q = q.where(Property.total_price <= max_price)
        if min_area is not None:
            q = q.where(Property.area >= min_area)
        if max_area is not None:
            q = q.where(Property.area <= max_area)
        if rooms is not None:
            q = q.where(Property.room_count == rooms)
        if property_type is not None:
            q = q.where(Property.property_type == property_type)
        if transaction_type is not None:
            q = q.where(Property.transaction_type == transaction_type)
        if status is not None:
            q = q.where(Property.status == status)
        if keyword:
            kw = f"%{keyword}%"
            q = q.where(or_(
                Property.title.like(kw),
                Property.description.like(kw),
                Property.detail_address.like(kw),
                Property.city.like(kw),
                Property.district.like(kw)
            ))
        return q

    # 获取总数
    count_q = _apply_filters(select(func.count()).select_from(Property))
    total_result = await db.execute(count_q)
    total = total_result.scalar()

    # 分页数据查询
    data_q = _apply_filters(select(Property))
    data_q = data_q.order_by(desc(Property.created_at))
    data_q = data_q.offset((page - 1) * page_size).limit(page_size)
    data_q = data_q.options(selectinload(Property.agent), selectinload(Property.images))

    result = await db.execute(data_q)
    properties = result.scalars().all()

    # 如果提供了用户位置，计算距离并进行筛选
    if user_lat is not None and user_lon is not None:
        properties_list = []
        for prop in properties:
            # 只计算有经纬度的房源的距离
            if prop.longitude is not None and prop.latitude is not None:
                distance = calculate_distance(
                    user_lat, user_lon,
                    float(prop.latitude), float(prop.longitude)
                )
                # 如果设置了最大距离且超过该距离，跳过
                if max_distance is not None and distance > max_distance:
                    continue
                # 将距离附加到房源对象上（作为动态属性）
                prop.distance = distance
                properties_list.append(prop)
            elif max_distance is None:
                # 没有距离限制时，也包含没有坐标的房源
                properties_list.append(prop)

        # 更新total（如果有距离筛选）
        if max_distance is not None:
            total = len(properties_list)

        return properties_list, total
    else:
        return list(properties), total


async def create_property(
    db: AsyncSession,
    property_data: PropertyCreate,
    owner_id: int
) -> Property:
    """创建新房源"""
    # 处理 images 字段 - 先提取 images，再排除 price 字段
    property_dict_full = property_data.model_dump()
    images = property_dict_full.get('images', None)
    property_dict = property_dict_full.copy()
    
    # 排除所有不在数据库模型中的字段
    invalid_fields = ['price', 'images', 'address', 'decoration', 'orientation', 'ownership', 'distance', 'community', 'room_type', 'floor']
    for field in invalid_fields:
        property_dict.pop(field, None)
    
    # 类型转换 - area 必须是 float
    if 'area' in property_dict:
        property_dict['area'] = float(property_dict['area'])
    
    # 如果有封面图，设置 cover_url
    if images and len(images) > 0:
        property_dict['cover_url'] = images[0]
    
    # 创建房源
    db_property = Property(
        **property_dict,
        agent_id=owner_id
    )
    db.add(db_property)
    await db.commit()
    await db.refresh(db_property)
    
    # 预加载 images 关系以避免序列化时出现懒加载问题
    result = await db.execute(
        select(Property)
        .where(Property.id == db_property.id)
        .options(selectinload(Property.images))
    )
    db_property = result.scalar_one()
    
    # 保存图片关联
    if images:
        from app.models.property import PropertyImage
        for i, img_url in enumerate(images):
            img = PropertyImage(
                property_id=db_property.id,
                image_url=img_url,
                is_cover=i == 0,
                sort_order=i
            )
            db.add(img)
        await db.commit()
    
    return db_property


async def update_property(
    db: AsyncSession,
    property_id: int,
    property_data: dict
) -> Optional[Property]:
    """更新房源信息"""
    property = await get_property_by_id(db, property_id)
    if not property:
        return None
    
    for key, value in property_data.items():
        if value is not None:
            setattr(property, key, value)
    
    await db.commit()
    await db.refresh(property)
    
    # 清除相关缓存
    cache_key = CacheKeys.property_detail(property_id)
    await cache_service.delete(cache_key)
    await cache_service.delete_pattern("properties:list:*")
    await cache_service.delete_pattern("properties:search:*")
    
    return property


async def delete_property(db: AsyncSession, property_id: int) -> bool:
    """删除房源（软删除）"""
    from datetime import datetime, timezone
    
    property = await get_property_by_id(db, property_id)
    if not property:
        return False
    
    # 软删除：设置deleted_at时间戳
    property.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(property)
    
    # 清除相关缓存
    cache_key = CacheKeys.property_detail(property_id)
    await cache_service.delete(cache_key)
    await cache_service.delete_pattern("properties:list:*")
    await cache_service.delete_pattern("properties:search:*")
    
    return True
