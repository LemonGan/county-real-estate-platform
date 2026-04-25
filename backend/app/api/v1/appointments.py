"""
预约管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate, AppointmentResponse, AppointmentListResponse
)

router = APIRouter()


def check_member_privilege(user: User) -> bool:
    """检查用户是否有会员权益"""
    if user.member_level == 0:
        return False
    if user.member_expire and user.member_expire > datetime.now():
        return True
    return False


async def create_appointment(db: AsyncSession, appointment_data, user_id: int):
    """创建预约"""
    from app.crud.appointment import create_appointment as crud_create
    return await crud_create(db, appointment_data, user_id)


@router.post("", response_model=AppointmentResponse, status_code=201, summary="创建预约")
async def create_appointment_endpoint(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新的看房预约"""
    # 检查会员权限
    is_member = check_member_privilege(current_user)
    
    if not is_member:
        # 非会员每天限制1次预约
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.count(Appointment.id)).where(
            Appointment.user_id == current_user.id,
            Appointment.created_at >= today_start
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        if count >= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="普通用户每天仅限1次预约，开通会员可无限制预约"
            )
    
    try:
        appointment = await create_appointment(db, appointment_data, current_user.id)
        return appointment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=AppointmentListResponse, summary="获取预约列表")
async def get_appointments_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status_filter: int = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的预约列表"""
    from app.crud.appointment import get_appointments

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
    """获取预约详情"""
    from app.crud.appointment import get_appointment_by_id

    appointment = await get_appointment_by_id(db, appointment_id, current_user.id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    return appointment


@router.delete("/{appointment_id}", summary="取消预约")
async def cancel_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """取消预约"""
    from app.crud.appointment import cancel_appointment as crud_cancel

    success = await crud_cancel(db, appointment_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在或无法取消"
        )

    return {"message": "取消成功"}


@router.put("/{appointment_id}/status", summary="更新预约状态")
async def update_appointment_status(
    appointment_id: int,
    new_status: int = Query(..., description="状态: 1待确认 2已确认 3已完成 4已取消"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新预约状态（经纪人或用户）"""
    from app.crud.appointment import update_status

    appointment = await update_status(db, appointment_id, new_status, current_user.id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    return appointment
