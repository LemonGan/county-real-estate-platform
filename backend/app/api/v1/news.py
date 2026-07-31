"""房产资讯 API。"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_user_optional
from app.core.database import get_db
from app.crud.news import (
    get_news_interaction_status,
    get_public_news_article,
    increment_news_view_count,
    list_public_news_articles,
    resolve_category_name,
    toggle_news_collect,
    toggle_news_like,
)
from app.models.user import User

router = APIRouter()


def _format_time(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if hasattr(value, "astimezone"):
        value = value.astimezone()
    return value.strftime("%Y-%m-%d %H:%M")


def _plain_text_summary(summary: str | None, content: str) -> str:
    if summary:
        return summary
    text = re.sub(r"<[^>]+>", " ", content or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:120]


async def _build_news_payload(db: AsyncSession, article, current_user_id: int | None = None) -> dict:
    interaction = None
    if current_user_id is not None:
        interaction = await get_news_interaction_status(db, article.id, current_user_id)
    author = article.author
    category_name = resolve_category_name(article.category, article.category_name)
    author_name = article.author_name or (author.nickname if author and author.nickname else None) or "房产资讯"
    author_avatar = article.author_avatar or (author.avatar if author and author.avatar else "")
    return {
        "id": article.id,
        "title": article.title,
        "summary": _plain_text_summary(article.summary, article.content),
        "content": article.content,
        "cover_url": article.cover_url or "",
        "category": article.category,
        "category_name": category_name,
        "tags": article.tags or [],
        "author": author_name,
        "author_avatar": author_avatar,
        "publish_time": _format_time(article.publish_time or article.created_at),
        "publish_time_text": _format_time(article.publish_time or article.created_at),
        "view_count": article.view_count or 0,
        "like_count": article.like_count or 0,
        "collect_count": article.collect_count or 0,
        "share_count": article.share_count or 0,
        "is_liked": interaction["is_liked"] if interaction else False,
        "is_collected": interaction["is_collected"] if interaction else False,
    }


@router.get("", summary="获取房产资讯列表")
async def get_news_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    category: str | None = Query(None, description="分类筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    articles, total = await list_public_news_articles(db, page=page, page_size=page_size, category=category)
    current_user_id = current_user.id if current_user else None
    items = [await _build_news_payload(db, article, current_user_id) for article in articles]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{news_id}", summary="获取资讯详情")
async def get_news_detail(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    article = await get_public_news_article(db, news_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资讯暂未发布")
    current_user_id = current_user.id if current_user else None
    return await _build_news_payload(db, article, current_user_id)


@router.post("/{news_id}/view", summary="增加资讯浏览量")
async def view_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
):
    count = await increment_news_view_count(db, news_id)
    if count is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资讯暂未发布")
    return {"view_count": count}


@router.post("/{news_id}/like", summary="点赞资讯")
async def like_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    article = await get_public_news_article(db, news_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资讯暂未发布")
    liked, count = await toggle_news_like(db, news_id, current_user.id)
    return {"is_liked": liked, "like_count": count}


@router.post("/{news_id}/collect", summary="收藏资讯")
async def collect_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    article = await get_public_news_article(db, news_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资讯暂未发布")
    collected, count = await toggle_news_collect(db, news_id, current_user.id)
    return {"is_collected": collected, "collect_count": count}
