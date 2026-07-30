"""用户反馈接口。"""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.feedback import Feedback
from app.models.user import User

router = APIRouter()

FeedbackCategory = Literal["general", "property", "agent", "feature", "bug"]


class FeedbackCreate(BaseModel):
    category: FeedbackCategory = "general"
    content: str = Field(min_length=1, max_length=500)
    contact: str | None = Field(default=None, max_length=100)


def _serialize_feedback(feedback: Feedback) -> dict:
    return {
        "id": feedback.id,
        "category": feedback.category,
        "content": feedback.content,
        "status": feedback.status,
        "admin_response": feedback.admin_response,
        "created_at": feedback.created_at,
        "handled_at": feedback.handled_at,
    }


@router.post("/feedback", status_code=201, summary="提交用户反馈")
async def submit_feedback(
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    feedback = Feedback(
        user_id=current_user.id,
        category=data.category,
        content=data.content.strip(),
        contact=data.contact.strip() if data.contact else None,
        source="miniprogram",
        status="pending",
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return {
        "id": feedback.id,
        "status": feedback.status,
        "message": "反馈已提交，我们会尽快处理",
    }


@router.get("/feedback/mine", summary="获取我的反馈记录")
async def get_my_feedback(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    condition = Feedback.user_id == current_user.id
    total = (await db.execute(
        select(func.count()).select_from(Feedback).where(condition)
    )).scalar_one()
    result = await db.execute(
        select(Feedback)
        .where(condition)
        .order_by(Feedback.created_at.desc(), Feedback.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [_serialize_feedback(feedback) for feedback in result.scalars().all()],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
