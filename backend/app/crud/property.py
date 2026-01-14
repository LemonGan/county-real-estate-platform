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
        .options(selectinload(Property.agent))
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
    # 构建查询
    query = select(Property).where(Property.deleted_at.is_(None))
    
    # 筛选条件
    if city:
        query = query.where(Property.city == city)
    if district:
        query = query.where(Property.district == district)
    if min_price is not None:
        query = query.where(Property.total_price >= min_price)
    if max_price is not None:
        query = query.where(Property.total_price <= max_price)
    if min_area is not None:
        query = query.where(Property.area >= min_area)
    if max_area is not None:
        query = query.where(Property.area <= max_area)
    if rooms is not None:
        query = query.where(Property.room_count == rooms)
    if property_type is not None:
        query = query.where(Property.property_type == property_type)
    if transaction_type is not None:
        query = query.where(Property.transaction_type == transaction_type)
    if status is not None:
        query = query.where(Property.status == status)
    
    # 关键词搜索（搜索标题、描述、地址）
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(
            or_(
                Property.title.like(keyword_pattern),
                Property.description.like(keyword_pattern),
                Property.detail_address.like(keyword_pattern),
                Property.city.like(keyword_pattern),
                Property.district.like(keyword_pattern)
            )
        )
    
    # 获取总数
    count_query = select(func.count()).select_from(Property).where(Property.deleted_at.is_(None))
    if city:
        count_query = count_query.where(Property.city == city)
    if district:
        count_query = count_query.where(Property.district == district)
    if min_price is not None:
        count_query = count_query.where(Property.total_price >= min_price)
    if max_price is not None:
        count_query = count_query.where(Property.total_price <= max_price)
    if min_area is not None:
        count_query = count_query.where(Property.area >= min_area)
    if max_area is not None:
        count_query = count_query.where(Property.area <= max_area)
    if rooms is not None:
        count_query = count_query.where(Property.room_count == rooms)
    if property_type is not None:
        count_query = count_query.where(Property.property_type == property_type)
    if transaction_type is not None:
        count_query = count_query.where(Property.transaction_type == transaction_type)
    if status is not None:
        count_query = count_query.where(Property.status == status)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        count_query = count_query.where(
            or_(
                Property.title.like(keyword_pattern),
                Property.description.like(keyword_pattern),
                Property.detail_address.like(keyword_pattern),
                Property.city.like(keyword_pattern),
                Property.district.like(keyword_pattern)
            )
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(desc(Property.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(selectinload(Property.agent))
    
    result = await db.execute(query)
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
    # 使用agent_id字段（owner_id作为参数名保持兼容）
    db_property = Property(
        **property_data.model_dump(),
        agent_id=owner_id
    )
    db.add(db_property)
    await db.commit()
    await db.refresh(db_property)
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
