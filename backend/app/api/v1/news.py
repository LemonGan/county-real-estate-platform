"""房产资讯 API。

资讯内容尚未接入运营后台前，接口只返回空列表，避免展示虚构文章。
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter()


@router.get("", summary="获取房产资讯列表")
async def get_news_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
):
    """资讯运营功能接入前不展示占位文章。"""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/{news_id}", summary="获取资讯详情")
async def get_news_detail(news_id: int):
    """没有已发布的资讯时，不伪造详情内容。"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="资讯暂未发布",
    )
