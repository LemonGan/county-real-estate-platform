"""
预约相关Schema
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime, date, time


class AppointmentBase(BaseModel):
    """预约基础信息"""
    property_id: int = Field(..., description="房源ID")
    appointment_time: datetime = Field(..., description="预约时间（完整日期时间）")
    contact_phone: str = Field(..., min_length=11, max_length=11, description="联系电话")
    contact_name: Optional[str] = Field(None, max_length=50, description="联系人姓名")
    remark: Optional[str] = Field(None, description="备注/留言")


class AppointmentCreate(AppointmentBase):
    """创建预约请求"""
    pass


class AppointmentResponse(BaseModel):
    """预约响应"""
    id: int
    user_id: int
    property_id: int
    agent_id: Optional[int] = None
    appointment_date: date
    appointment_time: time
    contact_name: str
    contact_phone: str
    special_requirements: Optional[str] = None
    remark: Optional[str] = Field(None, description="备注/留言")
    status: int
    created_at: datetime
    updated_at: datetime

    @field_serializer('appointment_time')
    def serialize_time(self, t: time) -> str:
        """序列化时间字段"""
        if t is None:
            return None
        return t.strftime('%H:%M:%S')

    @field_serializer('appointment_date')
    def serialize_date(self, d: date) -> str:
        """序列化日期字段"""
        if d is None:
            return None
        return d.isoformat()

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """预约列表响应"""
    list: list[AppointmentResponse]
    total: int
    page: int
    page_size: int
