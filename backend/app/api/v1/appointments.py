"""
看房预约管理API
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentListResponse
from app.crud.appointment import create_appointment, get_appointments, get_appointment_by_id, update_appointment
from app.models.appointment import AppointmentStatus

router = APIRouter()


@router.post("", response_model=AppointmentResponse, status_code=201, summary="创建看房预约")
async def create_appointment_endpoint(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新的看房预约（自动检测时间冲突）"""
    try:
        appointment = await create_appointment(db, appointment_data, current_user.id)
        return appointment
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=AppointmentListResponse, summary="获取预约列表")
async def get_appointments_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的预约列表"""
    appointments, total = await get_appointments(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    return {
        "list": appointments,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{appointment_id}", response_model=AppointmentResponse, summary="获取预约详情")
async def get_appointment_detail(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据ID获取预约详细信息"""
    appointment = await get_appointment_by_id(db, appointment_id=appointment_id)
    if not appointment:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    # 检查权限：只能查看自己的预约或相关房源的经纪人
    if appointment.user_id != current_user.id:
        # 如果是经纪人，检查是否是相关房源的经纪人
        if not (appointment.property and appointment.property.agent_id == current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此预约"
            )

    return appointment


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse, summary="取消预约")
async def cancel_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """取消预约（仅预约用户可取消）"""
    from fastapi import HTTPException, status

    appointment = await get_appointment_by_id(db, appointment_id=appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    # 检查权限：只能取消自己的预约
    if appointment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权取消此预约"
        )

    # 检查状态：只能取消待确认或已确认的预约
    if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该预约无法取消"
        )

    updated_appointment = await update_appointment(
        db,
        appointment_id=appointment_id,
        appointment_data={"status": AppointmentStatus.CANCELLED}
    )
    return updated_appointment


@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse, summary="取消预约（PUT兼容）")
async def cancel_appointment_put(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """取消预约（PUT方法，为前端兼容性保留）"""
    return await cancel_appointment(appointment_id, db, current_user)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse, summary="更新预约状态")
async def update_appointment_status(
    appointment_id: int,
    new_status: int = Query(..., ge=0, le=4, description="新状态：0待确认，1已确认，2已完成，3已取消，4已过期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新预约状态（仅相关用户可操作）"""
    from fastapi import HTTPException, status

    appointment = await get_appointment_by_id(db, appointment_id=appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    # 检查权限：预约用户或相关房源的经纪人
    if appointment.user_id != current_user.id:
        if not (appointment.property and appointment.property.agent_id == current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此预约状态"
            )

    updated_appointment = await update_appointment(
        db,
        appointment_id=appointment_id,
        appointment_data={"status": new_status}
    )
    return updated_appointment


@router.get("/agents/{agent_id}/available-slots", summary="获取经纪人可用时间段")
async def get_agent_available_slots_endpoint(
    agent_id: int,
    date: date = Query(..., description="查询日期（YYYY-MM-DD）"),
    db: AsyncSession = Depends(get_db)
):
    """获取指定经纪人在指定日期的可用时间段"""
    from app.utils.appointment import get_agent_available_slots

    available_slots = await get_agent_available_slots(db, agent_id, date)
    return {
        "agent_id": agent_id,
        "date": date.isoformat(),
        "available_slots": [slot.strftime("%H:%M") for slot in available_slots]
    }
