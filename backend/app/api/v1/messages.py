"""持久化站内通知 API。"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.message import Message
from app.models.user import User

router = APIRouter()


def serialize_message(message: Message) -> dict:
    return {
        "id": message.id,
        "title": message.title,
        "content": message.content,
        "type": message.type,
        "related_id": message.related_id,
        "is_read": message.is_read,
        "created_at": message.created_at,
        "read_at": message.read_at,
    }


async def create_message(
    db: AsyncSession,
    user_id: int,
    title: str,
    content: str,
    message_type: int = 1,
    related_id: Optional[int] = None,
) -> Message:
    """写入一条站内通知；调用方应在其主业务提交后调用。"""
    message = Message(
        user_id=user_id,
        title=title[:100],
        content=content,
        type=message_type,
        related_id=related_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("", summary="获取消息列表")
async def get_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_filter: Optional[int] = Query(None, description="消息类型：1系统通知，2预约提醒，3房源动态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = [Message.user_id == current_user.id]
    if type_filter is not None:
        filters.append(Message.type == type_filter)
    total = (await db.execute(select(func.count(Message.id)).where(*filters))).scalar() or 0
    unread_count = (await db.execute(select(func.count(Message.id)).where(*filters, Message.is_read.is_(False)))).scalar() or 0
    result = await db.execute(
        select(Message).where(*filters).order_by(Message.created_at.desc(), Message.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    messages = result.scalars().all()
    return {"list": [serialize_message(item) for item in messages], "total": total, "page": page, "page_size": page_size, "unread_count": unread_count}


@router.get("/unread-count", summary="获取未读消息数")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    unread_count = (await db.execute(
        select(func.count(Message.id)).where(Message.user_id == current_user.id, Message.is_read.is_(False))
    )).scalar() or 0
    return {"unread_count": unread_count}


@router.post("/{message_id}/read", summary="标记消息为已读")
async def mark_as_read(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    message = (await db.execute(select(Message).where(Message.id == message_id, Message.user_id == current_user.id))).scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    if not message.is_read:
        message.is_read = True
        message.read_at = datetime.now(timezone.utc)
        await db.commit()
    return {"message": "标记成功"}


@router.post("/read-all", summary="全部标记已读")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Message).where(Message.user_id == current_user.id, Message.is_read.is_(False)))
    for message in result.scalars().all():
        message.is_read = True
        message.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "全部已读"}
