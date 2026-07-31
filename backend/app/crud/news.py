"""资讯CRUD操作。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.news_article import NewsArticle
from app.models.news_interaction import NewsInteraction

CATEGORY_NAMES = {
    "market": "市场分析",
    "guide": "购房指南",
    "policy": "政策解读",
    "knowledge": "房产知识",
}


def resolve_category_name(category: str | None, category_name: str | None = None) -> str:
    if category_name:
        return category_name
    if category:
        return CATEGORY_NAMES.get(category, category)
    return "资讯"


async def get_public_news_article(db: AsyncSession, news_id: int) -> Optional[NewsArticle]:
    result = await db.execute(
        select(NewsArticle)
        .where(
            NewsArticle.id == news_id,
            NewsArticle.deleted_at.is_(None),
            NewsArticle.is_published.is_(True),
        )
        .options(selectinload(NewsArticle.author))
    )
    return result.scalar_one_or_none()


async def list_public_news_articles(
    db: AsyncSession,
    page: int,
    page_size: int,
    category: Optional[str] = None,
) -> tuple[list[NewsArticle], int]:
    conditions = [NewsArticle.deleted_at.is_(None), NewsArticle.is_published.is_(True)]
    if category and category != "all":
        conditions.append(NewsArticle.category == category)

    total = (await db.execute(
        select(func.count()).select_from(NewsArticle).where(and_(*conditions))
    )).scalar() or 0

    result = await db.execute(
        select(NewsArticle)
        .where(and_(*conditions))
        .order_by(NewsArticle.sort_order.desc(), NewsArticle.publish_time.desc(), NewsArticle.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(selectinload(NewsArticle.author))
    )
    return list(result.scalars().all()), total


async def get_or_create_interaction(db: AsyncSession, news_id: int, user_id: int) -> NewsInteraction:
    result = await db.execute(
        select(NewsInteraction).where(
            NewsInteraction.news_id == news_id,
            NewsInteraction.user_id == user_id,
        )
    )
    interaction = result.scalar_one_or_none()
    if interaction:
        return interaction
    interaction = NewsInteraction(news_id=news_id, user_id=user_id)
    db.add(interaction)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        result = await db.execute(
            select(NewsInteraction).where(
                NewsInteraction.news_id == news_id,
                NewsInteraction.user_id == user_id,
            )
        )
        interaction = result.scalar_one_or_none()
        if interaction:
            return interaction
        raise
    return interaction


async def increment_news_view_count(db: AsyncSession, news_id: int, user_id: Optional[int] = None) -> Optional[int]:
    article = await get_public_news_article(db, news_id)
    if not article:
        return None

    article.view_count = (article.view_count or 0) + 1
    if user_id is not None:
        interaction = await get_or_create_interaction(db, news_id, user_id)
        interaction.view_count = (interaction.view_count or 0) + 1
        interaction.last_viewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(article)
    return article.view_count or 0


async def toggle_news_like(db: AsyncSession, news_id: int, user_id: int) -> tuple[bool, int]:
    article = await get_public_news_article(db, news_id)
    if not article:
        return False, 0

    interaction = await get_or_create_interaction(db, news_id, user_id)
    liked = not bool(interaction.is_liked)
    interaction.is_liked = liked
    interaction.liked_at = datetime.now(timezone.utc) if liked else None

    article.like_count = max((article.like_count or 0) + (1 if liked else -1), 0)
    await db.commit()
    await db.refresh(article)
    return liked, article.like_count or 0


async def toggle_news_collect(db: AsyncSession, news_id: int, user_id: int) -> tuple[bool, int]:
    article = await get_public_news_article(db, news_id)
    if not article:
        return False, 0

    interaction = await get_or_create_interaction(db, news_id, user_id)
    collected = not bool(interaction.is_collected)
    interaction.is_collected = collected
    interaction.collected_at = datetime.now(timezone.utc) if collected else None

    article.collect_count = max((article.collect_count or 0) + (1 if collected else -1), 0)
    await db.commit()
    await db.refresh(article)
    return collected, article.collect_count or 0


async def get_news_interaction_status(db: AsyncSession, news_id: int, user_id: int) -> dict:
    result = await db.execute(
        select(NewsInteraction).where(
            NewsInteraction.news_id == news_id,
            NewsInteraction.user_id == user_id,
        )
    )
    interaction = result.scalar_one_or_none()
    return {
        "is_liked": bool(interaction.is_liked) if interaction else False,
        "is_collected": bool(interaction.is_collected) if interaction else False,
    }
