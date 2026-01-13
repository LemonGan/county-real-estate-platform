"""
经纪人管理API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.agent import (
    AgentResponse, AgentListResponse
)

router = APIRouter()


@router.get("", response_model=AgentListResponse, summary="获取经纪人列表")
async def get_agents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    is_verified: Optional[bool] = Query(None, description="是否实名认证"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取经纪人列表
    支持分页和筛选
    """
    # TODO: 从数据库获取经纪人列表
    # 这里暂时返回空列表
    agents = []
    total = 0

    return {
        "list": agents,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{agent_id}", response_model=AgentResponse, summary="获取经纪人详情")
async def get_agent_detail(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    根据ID获取经纪人详细信息
    包括基本信息、服务数据、房源列表等
    """
    # TODO: 从数据库获取经纪人详情
    # 这里暂时返回模拟数据
    mock_agent = {
        "id": agent_id,
        "nickname": "金牌经纪人",
        "avatar": "/assets/images/default-avatar.png",
        "avatar_url": "/assets/images/default-avatar.png",
        "phone": "138****8888",
        "company": "某某房产",
        "experience": 5,
        "rating": 4.8,
        "sales_count": 128,
        "service_count": 356,
        "introduction": "从事房产经纪行业5年，熟悉本地房源情况，服务热情周到，多次获得公司销售冠军。",
        "tags": ["金牌经纪人", "本地专家", "服务好"],
        "is_verified": True
    }

    return mock_agent


@router.post("/{agent_id}/follow/", summary="关注经纪人")
async def follow_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    关注/取消关注经纪人
    """
    # TODO: 实现关注/取消关注逻辑
    # 这里暂时返回成功
    return {
        "agent_id": agent_id,
        "user_id": current_user.id,
        "is_followed": True
    }


@router.get("/{agent_id}/properties", summary="获取经纪人房源列表")
async def get_agent_properties(
    agent_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[int] = Query(1, description="状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定经纪人的房源列表
    """
    # TODO: 从数据库获取经纪人的房源
    from app.crud.property import get_properties

    properties, total = await get_properties(
        db,
        page=page,
        page_size=page_size,
        agent_id=agent_id,
        status=status_filter
    )

    return {
        "list": properties,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{agent_id}/stats", summary="获取经纪人统计数据")
async def get_agent_stats(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取经纪人统计数据
    包括成交量、服务次数、评分等
    """
    # TODO: 从数据库获取统计数据
    return {
        "agent_id": agent_id,
        "sales_count": 128,
        "service_count": 356,
        "rating": 4.8,
        "experience": 5
    }
