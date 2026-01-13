"""
预约相关工具函数
"""
from datetime import date, time, datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.appointment import Appointment, AppointmentStatus


async def check_appointment_conflict(
    db: AsyncSession,
    agent_id: int,
    appointment_date: date,
    appointment_time: time,
    exclude_appointment_id: Optional[int] = None
) -> bool:
    """
    检查预约时间是否冲突
    
    Args:
        db: 数据库会话
        agent_id: 经纪人ID
        appointment_date: 预约日期
        appointment_time: 预约时间
        exclude_appointment_id: 排除的预约ID（用于更新时排除自己）
    
    Returns:
        True表示有冲突，False表示无冲突
    """
    # 构建查询：查找同一经纪人、同一日期、同一时间段的已确认或待确认预约
    query = select(Appointment).where(
        and_(
            Appointment.agent_id == agent_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_([
                AppointmentStatus.PENDING,
                AppointmentStatus.CONFIRMED
            ])
        )
    )
    
    # 排除指定的预约（用于更新时）
    if exclude_appointment_id:
        query = query.where(Appointment.id != exclude_appointment_id)
    
    result = await db.execute(query)
    conflicting_appointments = result.scalars().all()
    
    return len(conflicting_appointments) > 0


async def get_agent_available_slots(
    db: AsyncSession,
    agent_id: int,
    target_date: date
) -> List[time]:
    """
    获取经纪人某一天的可用时间段
    
    Args:
        db: 数据库会话
        agent_id: 经纪人ID
        target_date: 目标日期
    
    Returns:
        可用时间段列表
    """
    # 查找该日期已占用的时间段
    occupied_query = select(Appointment).where(
        and_(
            Appointment.agent_id == agent_id,
            Appointment.appointment_date == target_date,
            Appointment.status.in_([
                AppointmentStatus.PENDING,
                AppointmentStatus.CONFIRMED
            ])
        )
    )
    
    result = await db.execute(occupied_query)
    occupied_appointments = result.scalars().all()
    occupied_times = {apt.appointment_time for apt in occupied_appointments}
    
    # 定义标准时间段（9:00-18:00，每小时一个时段）
    all_slots = [
        time(9, 0), time(10, 0), time(11, 0), time(12, 0),
        time(13, 0), time(14, 0), time(15, 0), time(16, 0),
        time(17, 0), time(18, 0)
    ]
    
    # 返回未被占用的时间段
    available_slots = [slot for slot in all_slots if slot not in occupied_times]
    
    return available_slots
