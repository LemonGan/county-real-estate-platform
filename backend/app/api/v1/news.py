"""
房产资讯管理API
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.models.user import User

router = APIRouter()


@router.get("", summary="获取房产资讯列表")
async def get_news_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取房产资讯列表
    支持分页和分类筛选
    """
    # TODO: 实现资讯查询逻辑（需要news表）
    # 这里暂时返回模拟数据

    mock_news = [
        {
            "id": 1,
            "title": "2024年县城房地产市场走势分析",
            "summary": "随着城市化进程推进，县城房地产市场呈现新的发展态势...",
            "content": "随着城市化进程推进，县城房地产市场呈现新的发展态势。数据显示，返乡置业需求持续增长...",
            "cover_url": "/assets/images/news-cover-1.jpg",
            "category_name": "市场分析",
            "category": "market",
            "author": "房产研究院",
            "view_count": 1523,
            "created_at": "2024-01-15 10:30:00",
            "publish_time": "2小时前"
        },
        {
            "id": 2,
            "title": "买房必看：如何选择合适的房源",
            "summary": "选择房源时需要考虑的因素很多，包括地段、价格、配套等...",
            "content": "选择房源时需要考虑的因素很多，包括地段、价格、配套等...",
            "cover_url": "/assets/images/news-cover-2.jpg",
            "category_name": "购房指南",
            "category": "guide",
            "author": "房产顾问",
            "view_count": 892,
            "created_at": "2024-01-14 16:45:00",
            "publish_time": "昨天"
        },
        {
            "id": 3,
            "title": "房贷利率最新政策解读",
            "summary": "近期房贷政策有所调整，对购房者有哪些影响？",
            "content": "近期房贷政策有所调整，对购房者有哪些影响？...",
            "cover_url": "/assets/images/news-cover-3.jpg",
            "category_name": "政策解读",
            "category": "policy",
            "author": "金融分析师",
            "view_count": 2341,
            "created_at": "2024-01-13 09:20:00",
            "publish_time": "2天前"
        }
    ]

    return {
        "items": mock_news,
        "total": len(mock_news),
        "page": page,
        "page_size": page_size
    }


@router.get("/{news_id}", summary="获取资讯详情")
async def get_news_detail(
    news_id: int = Path(..., description="资讯ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取房产资讯详情"""
    # TODO: 实现资讯详情查询逻辑
    # 这里暂时返回模拟数据

    return {
        "id": news_id,
        "title": "2024年县城房地产市场走势分析",
        "summary": "随着城市化进程推进，县城房地产市场呈现新的发展态势...",
        "content": """
            <p>随着城市化进程推进，县城房地产市场呈现新的发展态势。</p>
            <p>数据显示，返乡置业需求持续增长，三四线城市和县城成为新的增长点。</p>
            <h3>市场特点</h3>
            <p>1. 价格相对稳定</p>
            <p>2. 政策支持力度大</p>
            <p>3. 改善型需求增加</p>
            <h3>购房建议</h3>
            <p>对于有意在县城置业的购房者，建议关注学区、交通、商业配套等因素。</p>
        """,
        "cover_url": "/assets/images/news-cover-1.jpg",
        "category_name": "市场分析",
        "category": "market",
        "author": "房产研究院",
        "author_avatar": "/assets/images/author-avatar.jpg",
        "view_count": 1523,
        "like_count": 128,
        "comment_count": 45,
        "created_at": "2024-01-15 10:30:00",
        "publish_time": "2小时前"
    }
