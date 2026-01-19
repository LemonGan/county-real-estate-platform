"""
预约CRUD操作
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment
from app.models.property import Property
from app.schemas.appointment import AppointmentCreate


async def get_appointment_by_id(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
    """根据ID获取预约"""
    result = await db.execute(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            selectinload(Appointment.property),
            selectinload(Appointment.user)
        )
    )
    return result.scalar_one_or_none()


async def get_appointments(
    db: AsyncSession,
    user_id: Optional[int] = None,
    property_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10
) -> Tuple[List[Appointment], int]:
    """获取预约列表（分页）"""
    # 构建查询
    query = select(Appointment)
    
    # 用户筛选
    if user_id:
        query = query.where(Appointment.user_id == user_id)
    
    # 房源筛选
    if property_id:
        query = query.where(Appointment.property_id == property_id)
    
    # 获取总数
    count_query = select(func.count()).select_from(Appointment)
    if user_id:
        count_query = count_query.where(Appointment.user_id == user_id)
    if property_id:
        count_query = count_query.where(Appointment.property_id == property_id)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(desc(Appointment.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(
        selectinload(Appointment.property),
        selectinload(Appointment.user)
    )
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    return list(appointments), total


async def create_appointment(
    db: AsyncSession,
    appointment_data: AppointmentCreate,
    user_id: int
) -> Appointment:
    """创建新预约"""
    # 获取房源信息以获取agent_id
    property_result = await db.execute(
        select(Property).where(Property.id == appointment_data.property_id)
    )
    property_obj = property_result.scalar_one_or_none()
    if not property_obj:
        raise ValueError("房源不存在")

    agent_id = property_obj.agent_id

    # 从datetime中分离date和time
    appointment_dt = appointment_data.appointment_time
    appointment_date = appointment_dt.date()
    appointment_time = appointment_dt.time()

    # 创建预约对象
    db_appointment = Appointment(
        user_id=user_id,
        property_id=appointment_data.property_id,
        agent_id=agent_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        contact_name=appointment_data.contact_name or "用户",
        contact_phone=appointment_data.contact_phone,
        special_requirements=appointment_data.remark,
        status=1  # 待确认
    )
    db.add(db_appointment)
    await db.commit()
    await db.refresh(db_appointment)
    return db_appointment


async def update_appointment(
    db: AsyncSession,
    appointment_id: int,
    appointment_data: dict
) -> Optional[Appointment]:
    """更新预约信息"""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        return None
    
    for key, value in appointment_data.items():
        if value is not None:
            setattr(appointment, key, value)
    
    await db.commit()
    await db.refresh(appointment)
    return appointment


async def delete_appointment(db: AsyncSession, appointment_id: int) -> bool:
    """删除预约"""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        return False
    
    await db.delete(appointment)
    await db.commit()
    return True
