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
from app.models.appointment import Appointment
from app.models.property import Property
from app.models.property_favorite import PropertyFavorite
from app.models.agent_follow import AgentFollow
from app.schemas.agent import (
    AgentResponse, AgentListResponse
)

router = APIRouter()


def _approved_agent_conditions():
    return (
        User.is_agent.is_(True),
        User.is_active.is_(True),
        User.agent_application_status == "approved",
    )


@router.get("/customers", summary="获取当前经纪人的客户列表")
async def get_agent_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, max_length=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """返回向当前经纪人预约过看房的客户，并对手机号脱敏。"""
    if not current_user.is_agent:
        raise HTTPException(status_code=403, detail="只有经纪人才能查看客户")

    conditions = [Appointment.agent_id == current_user.id]
    if keyword and keyword.strip():
        search = f"%{keyword.strip()}%"
        conditions.append((User.nickname.like(search)) | (User.phone.like(search)))

    total_stmt = select(func.count(func.distinct(Appointment.user_id))).join(
        User, User.id == Appointment.user_id
    ).where(and_(*conditions))
    total = (await db.execute(total_stmt)).scalar() or 0

    customers_stmt = select(User).join(
        Appointment, Appointment.user_id == User.id
    ).where(and_(*conditions)).distinct().order_by(User.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size)
    customers = (await db.execute(customers_stmt)).scalars().all()

    items = []
    for customer in customers:
        favorite_count = (await db.execute(
            select(func.count(PropertyFavorite.id)).where(PropertyFavorite.user_id == customer.id)
        )).scalar() or 0
        phone = customer.phone or ""
        masked_phone = f"{phone[:3]}****{phone[-4:]}" if len(phone) >= 7 else ""
        items.append({
            "id": customer.id,
            "nickname": customer.nickname or "用户",
            "avatar": customer.avatar or "",
            "phone": masked_phone,
            "current_city": customer.current_city,
            "hometown_city": customer.hometown_city,
            "favorite_count": favorite_count,
        })

    return {"list": items, "total": total, "page": page, "page_size": page_size}


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
    conditions = list(_approved_agent_conditions())
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
    agent_ids = [user.id for user in users]
    property_counts = {}
    sales_counts = {}
    service_counts = {}
    if agent_ids:
        property_rows = await db.execute(
            select(Property.agent_id, func.count(Property.id))
            .where(
                Property.agent_id.in_(agent_ids),
                Property.deleted_at.is_(None),
                Property.audit_status == 1,
                Property.status == 1,
            )
            .group_by(Property.agent_id)
        )
        property_counts = {agent_id: count for agent_id, count in property_rows.all()}
        sales_rows = await db.execute(
            select(Property.agent_id, func.count(Property.id))
            .where(
                Property.agent_id.in_(agent_ids),
                Property.deleted_at.is_(None),
                Property.audit_status == 1,
                Property.status == 2,
            )
            .group_by(Property.agent_id)
        )
        sales_counts = {agent_id: count for agent_id, count in sales_rows.all()}
        service_rows = await db.execute(
            select(Appointment.agent_id, func.count(Appointment.id))
            .where(Appointment.agent_id.in_(agent_ids), Appointment.status == 3)
            .group_by(Appointment.agent_id)
        )
        service_counts = {agent_id: count for agent_id, count in service_rows.all()}

    agents = []
    for user in users:
        agents.append({
            "id": user.id,
            "nickname": user.nickname or user.real_name or "经纪人",
            "avatar": user.avatar or None,
            "avatar_url": user.avatar or None,
            "company": user.agent_company or None,
            "sales_count": sales_counts.get(user.id, 0),
            "service_count": service_counts.get(user.id, 0),
            "property_count": property_counts.get(user.id, 0),
            "tags": [],
            "is_verified": user.is_verified,
        })

    return {"list": agents, "total": total, "page": page, "page_size": page_size}


# ========== 经纪人工作台API (必须在 /{agent_id} 之前) ==========

@router.get("/workbench", summary="获取工作台数据")
async def get_workbench(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前登录经纪人的工作台数据"""
    if not current_user.is_agent:
        raise HTTPException(status_code=403, detail="只有经纪人才能访问此接口")
    
    from sqlalchemy import select, func, and_
    
    # 统计房源数量
    prop_stmt = select(func.count(Property.id)).where(Property.agent_id == current_user.id)
    prop_result = await db.execute(prop_stmt)
    property_count = prop_result.scalar() or 0
    
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
        Appointment.status == 0  # 已取消
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


async def _get_public_agent_id(db: AsyncSession, agent_id: int) -> int:
    agent = (await db.execute(
        select(User.id).where(User.id == agent_id, *_approved_agent_conditions())
    )).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经纪人不存在或暂不可公开查看")
    return agent


@router.get("/{agent_id}/follow-status", summary="获取当前用户关注状态")
async def get_agent_follow_status(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _get_public_agent_id(db, agent_id)
    following = (await db.execute(
        select(AgentFollow.id).where(AgentFollow.user_id == current_user.id, AgentFollow.agent_id == agent_id)
    )).scalar_one_or_none() is not None
    follower_count = (await db.execute(
        select(func.count(AgentFollow.id)).where(AgentFollow.agent_id == agent_id)
    )).scalar() or 0
    return {"agent_id": agent_id, "following": following, "follower_count": follower_count}


@router.get("/{agent_id}", response_model=AgentResponse, summary="获取经纪人详情")
async def get_agent_detail(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """返回已审核经纪人的真实公开资料，不编造服务成绩或身份信息。"""
    user = (await db.execute(
        select(User).where(User.id == agent_id, *_approved_agent_conditions())
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经纪人不存在或暂不可公开查看")

    property_count = (await db.execute(
        select(func.count(Property.id)).where(
            Property.agent_id == user.id,
            Property.deleted_at.is_(None),
            Property.audit_status == 1,
            Property.status == 1,
        )
    )).scalar() or 0
    sales_count = (await db.execute(
        select(func.count(Property.id)).where(
            Property.agent_id == user.id,
            Property.deleted_at.is_(None),
            Property.audit_status == 1,
            Property.status == 2,
        )
    )).scalar() or 0
    service_count = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.agent_id == user.id,
            Appointment.status == 3,
        )
    )).scalar() or 0
    return {
        "id": user.id,
        "nickname": user.nickname or user.real_name or "经纪人",
        "avatar": user.avatar or None,
        "avatar_url": user.avatar or None,
        "company": user.agent_company or None,
        "sales_count": sales_count,
        "service_count": service_count,
        "property_count": property_count,
        "tags": [],
        "is_verified": user.is_verified,
    }


@router.post("/{agent_id}/follow/", summary="关注经纪人")
async def follow_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _get_public_agent_id(db, agent_id)
    if current_user.id == agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能关注自己")
    existing = (await db.execute(
        select(AgentFollow.id).where(AgentFollow.user_id == current_user.id, AgentFollow.agent_id == agent_id)
    )).scalar_one_or_none()
    changed = existing is None
    if changed:
        db.add(AgentFollow(user_id=current_user.id, agent_id=agent_id))
        await db.commit()
    follower_count = (await db.execute(
        select(func.count(AgentFollow.id)).where(AgentFollow.agent_id == agent_id)
    )).scalar() or 0
    return {"agent_id": agent_id, "following": True, "changed": changed, "follower_count": follower_count}


@router.delete("/{agent_id}/follow/", summary="取消关注经纪人")
async def unfollow_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _get_public_agent_id(db, agent_id)
    existing = (await db.execute(
        select(AgentFollow).where(AgentFollow.user_id == current_user.id, AgentFollow.agent_id == agent_id)
    )).scalar_one_or_none()
    changed = existing is not None
    if existing:
        await db.delete(existing)
        await db.commit()
    follower_count = (await db.execute(
        select(func.count(AgentFollow.id)).where(AgentFollow.agent_id == agent_id)
    )).scalar() or 0
    return {"agent_id": agent_id, "following": False, "changed": changed, "follower_count": follower_count}


@router.get("/{agent_id}/properties", summary="获取经纪人房源列表")
async def get_agent_properties(
    agent_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[int] = Query(1, description="公开列表仅支持在售状态（1）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定经纪人的房源列表
    """
    agent = (await db.execute(
        select(User.id).where(User.id == agent_id, *_approved_agent_conditions())
    )).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经纪人不存在或暂不可公开查看")
    if status_filter != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="公开列表仅支持查询在售房源")

    from app.crud.property import get_properties

    properties, total = await get_properties(
        db,
        page=page,
        page_size=page_size,
        agent_id=agent_id,
        status=1
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
    db: AsyncSession = Depends(get_db),
):
    """返回可由当前数据库验证的统计值。"""
    agent = (await db.execute(
        select(User.id).where(User.id == agent_id, *_approved_agent_conditions())
    )).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经纪人不存在或暂不可公开查看")
    property_count = (await db.execute(
        select(func.count(Property.id)).where(
            Property.agent_id == agent_id,
            Property.deleted_at.is_(None),
            Property.audit_status == 1,
            Property.status == 1,
        )
    )).scalar() or 0
    sales_count = (await db.execute(
        select(func.count(Property.id)).where(
            Property.agent_id == agent_id,
            Property.deleted_at.is_(None),
            Property.audit_status == 1,
            Property.status == 2,
        )
    )).scalar() or 0
    service_count = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.agent_id == agent_id,
            Appointment.status == 3,
        )
    )).scalar() or 0
    return {
        "agent_id": agent_id,
        "property_count": property_count,
        "sales_count": sales_count,
        "service_count": service_count,
    }
