"""预约相关 Schema。"""
from datetime import datetime, date, time, timedelta
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, field_validator


class AppointmentBase(BaseModel):
    """预约基础信息。"""

    property_id: int = Field(..., gt=0, description="房源ID")
    appointment_time: datetime = Field(..., description="预约时间（完整日期时间）")
    contact_phone: str = Field(..., min_length=11, max_length=11, description="联系电话")
    contact_name: Optional[str] = Field(None, max_length=50, description="联系人姓名")
    remark: Optional[str] = Field(None, max_length=500, description="备注/留言")

    @field_validator("appointment_time")
    @classmethod
    def validate_appointment_time(cls, value: datetime) -> datetime:
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value <= now:
            raise ValueError("预约时间必须晚于当前时间")
        if value.date() > (now + timedelta(days=90)).date():
            raise ValueError("预约时间不能超过未来90天")
        if value.minute != 0 or value.second != 0 or not 9 <= value.hour <= 20:
            raise ValueError("预约时间仅支持每日09:00至20:00的整点时段")
        return value

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, value: str) -> str:
        phone = value.strip()
        if len(phone) != 11 or not phone.isdigit() or phone[0] != "1" or phone[1] not in "3456789":
            raise ValueError("请输入正确的11位中国大陆手机号")
        return phone

    @field_validator("contact_name")
    @classmethod
    def normalize_contact_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("remark")
    @classmethod
    def normalize_remark(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class AppointmentCreate(AppointmentBase):
    """创建预约请求。"""


class AppointmentResponse(BaseModel):
    """预约响应。"""

    id: int
    user_id: int
    property_id: int
    agent_id: Optional[int] = None
    property: Optional[dict] = None
    agent: Optional[dict] = None
    appointment_date: date
    appointment_time: time
    contact_name: str
    contact_phone: str
    special_requirements: Optional[str] = None
    remark: Optional[str] = Field(None, description="备注/留言")
    status: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("appointment_time")
    def serialize_time(self, value: time) -> str:
        return value.strftime("%H:%M:%S")

    @field_serializer("appointment_date")
    def serialize_date(self, value: date) -> str:
        return value.isoformat()


class AppointmentListResponse(BaseModel):
    list: list[AppointmentResponse]
    total: int
    page: int
    page_size: int
