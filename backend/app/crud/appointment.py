"""预约 CRUD 与状态流转规则。"""
from datetime import datetime, timezone
from typing import Optional, Tuple, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment, AppointmentStatus
from app.models.property import Property
from app.models.user import User
from app.schemas.appointment import AppointmentCreate
from app.utils.appointment import check_appointment_conflict


ACTIVE_STATUSES = {AppointmentStatus.PENDING.value, AppointmentStatus.CONFIRMED.value}


def can_transition_status(
    current_status: int,
    target_status: int,
    *,
    is_owner: bool,
    is_assigned_agent: bool,
    is_superuser: bool,
) -> bool:
    """返回当前操作者是否可执行该预约状态变更。"""
    if target_status not in {status.value for status in AppointmentStatus}:
        return False
    if not (is_owner or is_assigned_agent or is_superuser):
        return False
    if current_status == target_status:
        return True
    if current_status not in ACTIVE_STATUSES:
        return False
    if is_superuser:
        return (current_status, target_status) in {
            (AppointmentStatus.PENDING.value, AppointmentStatus.CONFIRMED.value),
            (AppointmentStatus.PENDING.value, AppointmentStatus.CANCELLED.value),
            (AppointmentStatus.CONFIRMED.value, AppointmentStatus.COMPLETED.value),
            (AppointmentStatus.CONFIRMED.value, AppointmentStatus.CANCELLED.value),
        }
    if is_owner:
        return target_status == AppointmentStatus.CANCELLED.value
    if is_assigned_agent:
        return (current_status, target_status) in {
            (AppointmentStatus.PENDING.value, AppointmentStatus.CONFIRMED.value),
            (AppointmentStatus.PENDING.value, AppointmentStatus.CANCELLED.value),
            (AppointmentStatus.CONFIRMED.value, AppointmentStatus.COMPLETED.value),
            (AppointmentStatus.CONFIRMED.value, AppointmentStatus.CANCELLED.value),
        }
    return False


async def get_appointment_by_id(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
    result = await db.execute(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            selectinload(Appointment.property),
            selectinload(Appointment.user),
            selectinload(Appointment.agent),
        )
    )
    return result.scalar_one_or_none()


async def get_appointments(
    db: AsyncSession,
    *,
    user_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
) -> Tuple[List[Appointment], int]:
    """获取指定用户或经纪人的预约列表。"""
    conditions = []
    if user_id is not None:
        conditions.append(Appointment.user_id == user_id)
    if agent_id is not None:
        conditions.append(Appointment.agent_id == agent_id)
    if property_id is not None:
        conditions.append(Appointment.property_id == property_id)
    if status is not None:
        conditions.append(Appointment.status == status)

    query = select(Appointment)
    count_query = select(func.count()).select_from(Appointment)
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(Appointment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(
            selectinload(Appointment.property),
            selectinload(Appointment.user),
            selectinload(Appointment.agent),
        )
    )
    return list(result.scalars().all()), total


async def create_appointment(
    db: AsyncSession,
    appointment_data: AppointmentCreate,
    user_id: int,
) -> Appointment:
    """为公开、在售房源创建预约，并阻止同一经纪人时段冲突。"""
    property_result = await db.execute(
        select(Property).where(
            Property.id == appointment_data.property_id,
            Property.audit_status == 1,
            Property.status == 1,
        )
    )
    property_obj = property_result.scalar_one_or_none()
    if not property_obj:
        raise ValueError("房源不存在、未审核通过或当前不可预约")

    agent_result = await db.execute(
        select(User).where(
            User.id == property_obj.agent_id,
            User.is_active.is_(True),
            User.is_agent.is_(True),
            User.agent_application_status == "approved",
        )
    )
    if not agent_result.scalar_one_or_none():
        raise ValueError("该房源经纪人当前不可接待预约")

    appointment_dt = appointment_data.appointment_time
    appointment_date = appointment_dt.date()
    appointment_time = appointment_dt.time().replace(tzinfo=None)
    if await check_appointment_conflict(db, property_obj.agent_id, appointment_date, appointment_time):
        raise ValueError("该经纪人在此时段已有预约，请选择其他时间")

    appointment = Appointment(
        user_id=user_id,
        property_id=property_obj.id,
        agent_id=property_obj.agent_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        contact_name=appointment_data.contact_name or "用户",
        contact_phone=appointment_data.contact_phone,
        special_requirements=appointment_data.remark,
        status=AppointmentStatus.PENDING.value,
    )
    db.add(appointment)
    await db.commit()
    return await get_appointment_by_id(db, appointment.id)  # type: ignore[arg-type]


async def update_status(
    db: AsyncSession,
    appointment_id: int,
    target_status: int,
    actor: User,
) -> Optional[Appointment]:
    """按用户、经纪人和超级管理员的最小权限更新预约状态。"""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        return None

    is_owner = appointment.user_id == actor.id
    is_assigned_agent = (
        appointment.agent_id == actor.id
        and actor.is_agent
        and actor.agent_application_status == "approved"
    )
    if not can_transition_status(
        appointment.status,
        target_status,
        is_owner=is_owner,
        is_assigned_agent=is_assigned_agent,
        is_superuser=actor.is_superuser,
    ):
        raise PermissionError("当前账号无权执行该预约状态变更")

    if appointment.status == target_status:
        return appointment

    appointment.status = target_status
    now = datetime.now(timezone.utc)
    if target_status == AppointmentStatus.CANCELLED.value:
        appointment.cancel_time = now
        appointment.cancel_reason = "用户取消" if is_owner and not is_superuser else "经纪人或后台取消"
    elif target_status == AppointmentStatus.CONFIRMED.value:
        appointment.confirmed_at = now
    elif target_status == AppointmentStatus.COMPLETED.value:
        appointment.completed_at = now
    await db.commit()
    return await get_appointment_by_id(db, appointment_id)


async def cancel_appointment(db: AsyncSession, appointment_id: int, actor: User) -> Optional[Appointment]:
    return await update_status(db, appointment_id, AppointmentStatus.CANCELLED.value, actor)
