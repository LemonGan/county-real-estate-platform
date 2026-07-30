"""预约管理 API。"""
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.v1.messages import create_message
from app.core.database import get_db
from app.crud.appointment import (
    cancel_appointment as crud_cancel,
    create_appointment,
    get_appointment_by_id,
    get_appointments,
    update_status,
)
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentListResponse, AppointmentResponse

router = APIRouter()


async def notify_user(
    db: AsyncSession,
    user_id: int,
    title: str,
    content: str,
    related_id: int,
) -> None:
    """通知写入失败不回滚已成功提交的预约主业务。"""
    try:
        await create_message(db, user_id, title, content, message_type=2, related_id=related_id, related_type="appointment")
    except Exception:
        await db.rollback()


def serialize_appointment(appointment: Appointment) -> dict:
    property_item = appointment.property
    agent = appointment.agent
    return {
        "id": appointment.id,
        "user_id": appointment.user_id,
        "property_id": appointment.property_id,
        "agent_id": appointment.agent_id,
        "appointment_date": appointment.appointment_date,
        "appointment_time": appointment.appointment_time,
        "contact_name": appointment.contact_name,
        "contact_phone": appointment.contact_phone,
        "special_requirements": appointment.special_requirements,
        "remark": appointment.special_requirements,
        "status": appointment.status,
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at,
        "property": {
            "id": property_item.id,
            "title": property_item.title,
            "address": property_item.detail_address or "",
            "cover_url": property_item.cover_url or "",
        } if property_item else None,
        "agent": {
            "id": agent.id,
            "nickname": agent.nickname or agent.real_name or "经纪人",
            "phone": agent.phone or "",
        } if agent else None,
    }


def require_agent_scope(user: User) -> None:
    if not user.is_agent or user.agent_application_status != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有审核通过的经纪人才能查看接待预约")


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED, summary="创建预约")
async def create_appointment_endpoint(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新的看房预约；当前版本每位用户每天最多提交一次。"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.user_id == current_user.id,
            Appointment.created_at >= today_start,
        )
    )).scalar() or 0
    if count >= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="每位用户每天仅限提交1次预约，请明天再试")

    try:
        appointment = await create_appointment(db, appointment_data, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    property_title = appointment.property.title if appointment.property else "房源"
    await notify_user(
        db,
        appointment.agent_id,
        "收到新的看房预约",
        f"您收到“{property_title}”的预约，请及时确认接待安排。",
        appointment.id,
    )
    return serialize_appointment(appointment)


@router.get("", response_model=AppointmentListResponse, summary="获取预约列表")
async def get_appointments_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status_filter: Optional[int] = Query(None, alias="status", ge=0, le=3, description="状态筛选"),
    view: Literal["user", "agent"] = Query("user", description="查看本人预约或接待预约"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """普通用户仅能查看自己的预约；经纪人可显式查看分配给自己的预约。"""
    if view == "agent":
        require_agent_scope(current_user)
        appointments, total = await get_appointments(
            db, agent_id=current_user.id, status=status_filter, page=page, page_size=page_size
        )
    else:
        appointments, total = await get_appointments(
            db, user_id=current_user.id, status=status_filter, page=page, page_size=page_size
        )
    return {"list": [serialize_appointment(item) for item in appointments], "total": total, "page": page, "page_size": page_size}


@router.get("/{appointment_id}", response_model=AppointmentResponse, summary="获取预约详情")
async def get_appointment_detail(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    is_assigned_agent = (
        appointment.agent_id == current_user.id
        and current_user.is_agent
        and current_user.agent_application_status == "approved"
    )
    if appointment.user_id != current_user.id and not is_assigned_agent and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此预约")
    return serialize_appointment(appointment)


@router.delete("/{appointment_id}", response_model=AppointmentResponse, summary="取消预约")
async def cancel_appointment_endpoint(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        appointment = await crud_cancel(db, appointment_id, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    if appointment.agent_id != current_user.id:
        property_title = appointment.property.title if appointment.property else "房源"
        await notify_user(
            db,
            appointment.agent_id,
            "预约已取消",
            f"“{property_title}”的一条看房预约已被用户取消。",
            appointment.id,
        )
    return serialize_appointment(appointment)


@router.put("/{appointment_id}/status", response_model=AppointmentResponse, summary="更新预约状态")
async def update_appointment_status(
    appointment_id: int,
    new_status: int = Query(..., ge=0, le=3, description="状态：0已取消、1待确认、2已确认、3已完成"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    previous = await get_appointment_by_id(db, appointment_id)
    previous_status = previous.status if previous else None
    try:
        appointment = await update_status(db, appointment_id, new_status, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    if appointment.status != previous_status and appointment.user_id != current_user.id:
        status_text = {
            AppointmentStatus.CANCELLED.value: "已取消",
            AppointmentStatus.CONFIRMED.value: "已确认",
            AppointmentStatus.COMPLETED.value: "已完成",
        }.get(appointment.status, "已更新")
        property_title = appointment.property.title if appointment.property else "房源"
        await notify_user(
            db,
            appointment.user_id,
            f"预约{status_text}",
            f"“{property_title}”的看房预约{status_text}，可在我的预约中查看详情。",
            appointment.id,
        )
    return serialize_appointment(appointment)
