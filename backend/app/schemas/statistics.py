"""
数据统计相关Schema
"""
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


class PropertyStatisticsResponse(BaseModel):
    """房源统计响应"""
    total: int
    status: Dict[str, int]  # {"on_sale": 0, "sold": 0, "offline": 0}
    transaction_type: Dict[str, int]  # {"sale": 0, "rent": 0}
    property_type: Dict[str, int]  # {"residential": 0, "shop": 0, "office": 0, "villa": 0}
    today_new: int
    avg_price: float


class UserStatisticsResponse(BaseModel):
    """用户统计响应"""
    total: int
    active_users: int  # 最近30天活跃用户
    agent_count: int
    today_new: int


class AppointmentStatisticsResponse(BaseModel):
    """预约统计响应"""
    total: int
    status: Dict[str, int]  # {"pending": 0, "confirmed": 0, "completed": 0, "cancelled": 0}
    today_new: int
    pending_count: int


class FavoriteStatisticsResponse(BaseModel):
    """收藏统计响应"""
    total: int
    today_new: int
    user_count: int


class DashboardStatisticsResponse(BaseModel):
    """仪表盘综合统计响应"""
    property: PropertyStatisticsResponse
    user: UserStatisticsResponse
    appointment: AppointmentStatisticsResponse
    favorite: FavoriteStatisticsResponse
    updated_at: str
