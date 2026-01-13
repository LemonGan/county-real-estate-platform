"""
预约相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    """预约基础信息"""
    property_id: int = Field(..., description="房源ID")
    appointment_time: datetime = Field(..., description="预约时间")
    contact_phone: str = Field(..., min_length=11, max_length=11, description="联系电话")
    contact_name: Optional[str] = Field(None, max_length=50, description="联系人姓名")
    message: Optional[str] = Field(None, description="留言")


class AppointmentCreate(AppointmentBase):
    """创建预约请求"""
    pass


class AppointmentResponse(AppointmentBase):
    """预约响应"""
    id: int
    user_id: int
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """预约列表响应"""
    list: list[AppointmentResponse]
    total: int
    page: int
    page_size: int
