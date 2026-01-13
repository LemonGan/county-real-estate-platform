"""
数据统计API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.statistics import (
    PropertyStatisticsResponse,
    UserStatisticsResponse,
    AppointmentStatisticsResponse,
    FavoriteStatisticsResponse,
    DashboardStatisticsResponse
)
from app.crud.statistics import (
    get_property_statistics,
    get_user_statistics,
    get_appointment_statistics,
    get_favorite_statistics,
    get_dashboard_statistics
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStatisticsResponse, summary="获取仪表盘综合统计")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取仪表盘综合统计数据（需要登录）"""
    # 可以添加权限检查，例如只有管理员或经纪人可以查看
    stats = await get_dashboard_statistics(db)
    return stats


@router.get("/properties", response_model=PropertyStatisticsResponse, summary="获取房源统计")
async def get_property_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取房源统计数据"""
    stats = await get_property_statistics(db)
    return stats


@router.get("/users", response_model=UserStatisticsResponse, summary="获取用户统计")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户统计数据"""
    stats = await get_user_statistics(db)
    return stats


@router.get("/appointments", response_model=AppointmentStatisticsResponse, summary="获取预约统计")
async def get_appointment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取预约统计数据"""
    stats = await get_appointment_statistics(db)
    return stats


@router.get("/favorites", response_model=FavoriteStatisticsResponse, summary="获取收藏统计")
async def get_favorite_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取收藏统计数据"""
    stats = await get_favorite_statistics(db)
    return stats


@router.get("/hot-search", summary="获取热门搜索关键词")
async def get_hot_search(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    获取热门搜索关键词
    返回用户搜索最频繁的关键词列表
    """
    # TODO: 实现热门搜索查询逻辑（需要search_logs表）
    # 这里暂时返回模拟数据

    hot_keywords = [
        {"keyword": "两室一厅", "count": 1523},
        {"keyword": "学区房", "count": 1245},
        {"keyword": "南北通透", "count": 982},
        {"keyword": "精装修", "count": 876},
        {"keyword": "新房", "count": 765},
        {"keyword": "二手房", "count": 654},
        {"keyword": "电梯房", "count": 543},
        {"keyword": "急售", "count": 432},
        {"keyword": "拎包入住", "count": 321},
        {"keyword": "低楼层", "count": 210}
    ]

    return {
        "keywords": hot_keywords[:limit]
    }
