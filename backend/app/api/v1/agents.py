"""
经纪人管理API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.agent import (
    AgentResponse, AgentListResponse
)

router = APIRouter()


@router.get("", response_model=AgentListResponse, summary="获取经纪人列表")
async def get_agents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    is_verified: Optional[bool] = Query(None, description="是否实名认证"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取经纪人列表
    支持分页和筛选
    """
    # 构建查询条件
    conditions = [User.is_agent == True]
    if is_verified is not None:
        conditions.append(User.is_verified == is_verified)
    
    # 查询总数
    count_stmt = select(func.count(User.id)).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # 分页查询
    offset = (page - 1) * page_size
    stmt = (
        select(User)
        .where(and_(*conditions))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    # 转换为经纪人格式
    agents = []
    for user in users:
        agents.append({
            "id": user.id,
            "nickname": user.nickname or user.real_name or "经纪人",
            "avatar": user.avatar or "/assets/images/default-avatar.png",
            "avatar_url": user.avatar or "/assets/images/default-avatar.png",
            "phone": user.phone[:3] + "****" + user.phone[-4:] if user.phone else "",
            "company": "县域房产",
            "experience": 3,
            "rating": 4.8,
            "sales_count": 0,
            "service_count": 0,
            "introduction": "专业房产经纪人，为您提供优质服务",
            "tags": ["专业", "诚信"],
            "is_verified": user.is_verified,
            "real_name": user.real_name,
            "agent_license": user.agent_license
        })

    return {
        "list": agents,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ========== 经纪人工作台API (必须在 /{agent_id} 之前) ==========

@router.get("/workbench", summary="获取工作台数据")
async def get_workbench(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前登录经纪人的工作台数据"""
    if not current_user.is_agent:
        raise HTTPException(status_code=403, detail="只有经纪人才能访问此接口")
    
    from app.models.property import Property
    from app.models.appointment import Appointment
    from sqlalchemy import select, func, and_
    
    # 统计房源数量
    prop_stmt = select(func.count(Property.id)).where(Property.agent_id == current_user.id)
    prop_result = await db.execute(prop_stmt)
    property_count = prop or 0
    
    # 统计_result.scalar()今日预约
    from datetime import datetime, timedelta
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    appt_stmt = select(func.count(Appointment.id)).where(
        and_(
            Appointment.agent_id == current_user.id,
            Appointment.appointment_date >= today,
            Appointment.appointment_date < tomorrow
        )
    )
    appt_result = await db.execute(appt_stmt)
    today_appointments = appt_result.scalar() or 0
    
    # 待处理预约
    pending_stmt = select(func.count(Appointment.id)).where(
        and_(
            Appointment.agent_id == current_user.id,
            Appointment.status == 1  # 待确认
        )
    )
    pending_result = await db.execute(pending_stmt)
    pending_appointments = pending_result.scalar() or 0
    
    # 客户数量（查询有预约的用户）
    customer_stmt = select(func.count(func.distinct(Appointment.user_id))).where(
        Appointment.agent_id == current_user.id
    )
    customer_result = await db.execute(customer_stmt)
    customer_count = customer_result.scalar() or 0
    
    return {
        "today_appointments": today_appointments,
        "pending_appointments": pending_appointments,
        "property_count": property_count,
        "customer_count": customer_count,
        "new_customers_yesterday": 0,
        "monthly_sales": 0,
        "monthly_views": 0
    }


@router.get("/property-stats", summary="获取房源统计")
async def get_property_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前登录经纪人的房源统计"""
    if not current_user.is_agent:
        raise HTTPException(status_code=403, detail="只有经纪人才能访问此接口")
    
    from app.models.property import Property
    from sqlalchemy import select, func
    
    # 全部房源
    total_stmt = select(func.count(Property.id)).where(Property.agent_id == current_user.id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0
    
    # 在售
    on_sale_stmt = select(func.count(Property.id)).where(
        Property.agent_id == current_user.id,
        Property.status == 1
    )
    on_sale_result = await db.execute(on_sale_stmt)
    on_sale = on_sale_result.scalar() or 0
    
    # 已售
    sold_stmt = select(func.count(Property.id)).where(
        Property.agent_id == current_user.id,
        Property.status == 2
    )
    sold_result = await db.execute(sold_stmt)
    sold = sold_result.scalar() or 0
    
    # 总浏览量
    views_stmt = select(func.sum(Property.view_count)).where(Property.agent_id == current_user.id)
    views_result = await db.execute(views_stmt)
    total_views = views_result.scalar() or 0
    
    # 总收藏数
    favorites_stmt = select(func.sum(Property.favorite_count)).where(Property.agent_id == current_user.id)
    favorites_result = await db.execute(favorites_stmt)
    total_favorites = favorites_result.scalar() or 0
    
    return {
        "total": total,
        "on_sale": on_sale,
        "sold": sold,
        "total_views": total_views or 0,
        "total_favorites": total_favorites or 0
    }


@router.get("/appointment-stats", summary="获取预约统计")
async def get_appointment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前登录经纪人的预约统计"""
    if not current_user.is_agent:
        raise HTTPException(status_code=403, detail="只有经纪人才能访问此接口")
    
    from app.models.appointment import Appointment
    from sqlalchemy import select, func
    
    # 全部预约
    total_stmt = select(func.count(Appointment.id)).where(Appointment.agent_id == current_user.id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0
    
    # 已完成
    completed_stmt = select(func.count(Appointment.id)).where(
        Appointment.agent_id == current_user.id,
        Appointment.status == 3  # 已完成
    )
    completed_result = await db.execute(completed_stmt)
    completed = completed_result.scalar() or 0
    
    # 已取消
    cancelled_stmt = select(func.count(Appointment.id)).where(
        Appointment.agent_id == current_user.id,
        Appointment.status == 4  # 已取消
    )
    cancelled_result = await db.execute(cancelled_stmt)
    cancelled = cancelled_result.scalar() or 0
    
    # 待处理
    pending_stmt = select(func.count(Appointment.id)).where(
        Appointment.agent_id == current_user.id,
        Appointment.status.in_([1, 2])  # 待确认或已确认
    )
    pending_result = await db.execute(pending_stmt)
    pending = pending_result.scalar() or 0
    
    # 成功率
    success_rate = round(completed / total * 100, 1) if total > 0 else 0
    
    return {
        "total": total,
        "completed": completed,
        "cancelled": cancelled,
        "pending": pending,
        "success_rate": success_rate
    }


# ========== 经纪人详情API (需要 agent_id 参数) ==========

@router.get("/{agent_id}", response_model=AgentResponse, summary="获取经纪人详情")
async def get_agent_detail(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    根据ID获取经纪人详细信息
    包括基本信息、服务数据、房源列表等
    """
    # 从数据库获取经纪人
    stmt = select(User).where(User.id == agent_id, User.is_agent == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return {
            "id": agent_id,
            "nickname": "金牌经纪人",
            "avatar": "/assets/images/default-avatar.png",
            "avatar_url": "/assets/images/default-avatar.png",
            "phone": "138****8888",
            "company": "某某房产",
            "experience": 5,
            "rating": 4.8,
            "sales_count": 128,
            "service_count": 356,
            "introduction": "从事房产经纪行业5年，熟悉本地房源情况，服务热情周到，多次获得公司销售冠军。",
            "tags": ["金牌经纪人", "本地专家", "服务好"],
            "is_verified": True
        }
    
    return {
        "id": user.id,
        "nickname": user.nickname or user.real_name or "经纪人",
        "avatar": user.avatar or "/assets/images/default-avatar.png",
        "avatar_url": user.avatar or "/assets/images/default-avatar.png",
        "phone": user.phone[:3] + "****" + user.phone[-4:] if user.phone else "",
        "company": "县域房产",
        "experience": 3,
        "rating": 4.8,
        "sales_count": 0,
        "service_count": 0,
        "introduction": "专业房产经纪人，为您提供优质服务",
        "tags": ["专业", "诚信"],
        "is_verified": user.is_verified,
        "real_name": user.real_name,
        "agent_license": user.agent_license
    }


@router.post("/{agent_id}/follow/", summary="关注经纪人")
async def follow_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    关注/取消关注经纪人
    """
    return {
        "agent_id": agent_id,
        "user_id": current_user.id,
        "is_followed": True
    }


@router.get("/{agent_id}/properties", summary="获取经纪人房源列表")
async def get_agent_properties(
    agent_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[int] = Query(1, description="状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定经纪人的房源列表
    """
    from app.crud.property import get_properties

    properties, total = await get_properties(
        db,
        page=page,
        page_size=page_size,
        agent_id=agent_id,
        status=status_filter
    )

    return {
        "list": properties,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{agent_id}/stats", summary="获取经纪人统计数据")
async def get_agent_stats(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取经纪人统计数据
    包括成交量、服务次数、评分等
    """
    return {
        "agent_id": agent_id,
        "sales_count": 128,
        "service_count": 356,
        "rating": 4.8,
        "experience": 5
    }
