"""
数据统计CRUD操作
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.models.user import User
from app.models.appointment import Appointment
from app.models.property_favorite import PropertyFavorite
from app.models.user_behavior import UserBehavior
from app.core.cache import cache_service, CacheKeys, CacheTTL


async def get_property_statistics(db: AsyncSession) -> Dict[str, Any]:
    """获取房源统计数据"""
    # 总房源数
    total_result = await db.execute(
        select(func.count(Property.id))
        .where(Property.deleted_at.is_(None))
    )
    total = total_result.scalar() or 0
    
    # 按状态统计
    status_result = await db.execute(
        select(
            Property.status,
            func.count(Property.id).label('count')
        )
        .where(Property.deleted_at.is_(None))
        .group_by(Property.status)
    )
    status_stats = {row.status: row.count for row in status_result.all()}
    
    # 按交易类型统计
    transaction_result = await db.execute(
        select(
            Property.transaction_type,
            func.count(Property.id).label('count')
        )
        .where(Property.deleted_at.is_(None))
        .group_by(Property.transaction_type)
    )
    transaction_stats = {row.transaction_type: row.count for row in transaction_result.all()}
    
    # 按房产类型统计
    property_type_result = await db.execute(
        select(
            Property.property_type,
            func.count(Property.id).label('count')
        )
        .where(Property.deleted_at.is_(None))
        .group_by(Property.property_type)
    )
    property_type_stats = {row.property_type: row.count for row in property_type_result.all()}
    
    # 今日新增房源
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_result = await db.execute(
        select(func.count(Property.id))
        .where(
            and_(
                Property.deleted_at.is_(None),
                Property.created_at >= today_start,
                Property.created_at < today_end + timedelta(days=1)
            )
        )
    )
    today_new = today_result.scalar() or 0
    
    # 平均价格（在售房源）
    avg_price_result = await db.execute(
        select(func.avg(Property.total_price))
        .where(
            and_(
                Property.deleted_at.is_(None),
                Property.status == 1,  # 在售
                Property.total_price.isnot(None)
            )
        )
    )
    avg_price = float(avg_price_result.scalar() or 0)
    
    return {
        "total": total,
        "status": {
            "on_sale": status_stats.get(1, 0),  # 在售
            "sold": status_stats.get(2, 0),     # 已售
            "offline": status_stats.get(3, 0)   # 下架
        },
        "transaction_type": {
            "sale": transaction_stats.get(1, 0),  # 出售
            "rent": transaction_stats.get(2, 0)    # 出租
        },
        "property_type": {
            "residential": property_type_stats.get(1, 0),  # 住宅
            "shop": property_type_stats.get(2, 0),         # 商铺
            "office": property_type_stats.get(3, 0),        # 写字楼
            "villa": property_type_stats.get(4, 0)          # 别墅
        },
        "today_new": today_new,
        "avg_price": round(avg_price, 2)
    }


async def get_user_statistics(db: AsyncSession) -> Dict[str, Any]:
    """获取用户统计数据"""
    # 总用户数
    total_result = await db.execute(
        select(func.count(User.id))
        .where(User.deleted_at.is_(None))
    )
    total = total_result.scalar() or 0
    
    # 活跃用户数（最近30天登录）
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_result = await db.execute(
        select(func.count(User.id))
        .where(
            and_(
                User.deleted_at.is_(None),
                User.last_login_at.isnot(None),
                User.last_login_at >= thirty_days_ago
            )
        )
    )
    active_users = active_result.scalar() or 0
    
    # 经纪人数量
    agent_result = await db.execute(
        select(func.count(User.id))
        .where(
            and_(
                User.deleted_at.is_(None),
                User.is_agent == True
            )
        )
    )
    agent_count = agent_result.scalar() or 0
    
    # 今日新增用户
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_result = await db.execute(
        select(func.count(User.id))
        .where(
            and_(
                User.deleted_at.is_(None),
                User.created_at >= today_start,
                User.created_at < today_end + timedelta(days=1)
            )
        )
    )
    today_new = today_result.scalar() or 0
    
    return {
        "total": total,
        "active_users": active_users,
        "agent_count": agent_count,
        "today_new": today_new
    }


async def get_appointment_statistics(db: AsyncSession) -> Dict[str, Any]:
    """获取预约统计数据"""
    # 总预约数
    total_result = await db.execute(
        select(func.count(Appointment.id))
        .where(Appointment.deleted_at.is_(None))
    )
    total = total_result.scalar() or 0
    
    # 按状态统计
    status_result = await db.execute(
        select(
            Appointment.confirmation_status,
            func.count(Appointment.id).label('count')
        )
        .where(Appointment.deleted_at.is_(None))
        .group_by(Appointment.confirmation_status)
    )
    status_stats = {row.confirmation_status: row.count for row in status_result.all()}
    
    # 今日新增预约
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_result = await db.execute(
        select(func.count(Appointment.id))
        .where(
            and_(
                Appointment.deleted_at.is_(None),
                Appointment.created_at >= today_start,
                Appointment.created_at < today_end + timedelta(days=1)
            )
        )
    )
    today_new = today_result.scalar() or 0
    
    # 待确认预约数
    pending_result = await db.execute(
        select(func.count(Appointment.id))
        .where(
            and_(
                Appointment.deleted_at.is_(None),
                Appointment.confirmation_status == 0  # 待确认
            )
        )
    )
    pending_count = pending_result.scalar() or 0
    
    return {
        "total": total,
        "status": {
            "pending": status_stats.get(0, 0),      # 待确认
            "confirmed": status_stats.get(1, 0),    # 已确认
            "completed": status_stats.get(2, 0),    # 已完成
            "cancelled": status_stats.get(3, 0)      # 已取消
        },
        "today_new": today_new,
        "pending_count": pending_count
    }


async def get_favorite_statistics(db: AsyncSession) -> Dict[str, Any]:
    """获取收藏统计数据"""
    # 总收藏数
    total_result = await db.execute(
        select(func.count(PropertyFavorite.id))
    )
    total = total_result.scalar() or 0
    
    # 今日新增收藏
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_result = await db.execute(
        select(func.count(PropertyFavorite.id))
        .where(
            and_(
                PropertyFavorite.created_at >= today_start,
                PropertyFavorite.created_at < today_end + timedelta(days=1)
            )
        )
    )
    today_new = today_result.scalar() or 0
    
    # 收藏用户数（去重）
    user_count_result = await db.execute(
        select(func.count(func.distinct(PropertyFavorite.user_id)))
    )
    user_count = user_count_result.scalar() or 0
    
    return {
        "total": total,
        "today_new": today_new,
        "user_count": user_count
    }


async def get_dashboard_statistics(db: AsyncSession, use_cache: bool = True) -> Dict[str, Any]:
    """获取仪表盘综合统计数据（支持缓存）"""
    # 尝试从缓存获取
    if use_cache:
        cached = await cache_service.get(CacheKeys.statistics_dashboard())
        if cached:
            return cached
    
    property_stats = await get_property_statistics(db)
    user_stats = await get_user_statistics(db)
    appointment_stats = await get_appointment_statistics(db)
    favorite_stats = await get_favorite_statistics(db)
    
    result = {
        "property": property_stats,
        "user": user_stats,
        "appointment": appointment_stats,
        "favorite": favorite_stats,
        "updated_at": datetime.now().isoformat()
    }
    
    # 缓存结果
    if use_cache:
        await cache_service.set(CacheKeys.statistics_dashboard(), result, CacheTTL.STATISTICS)
    
    return result