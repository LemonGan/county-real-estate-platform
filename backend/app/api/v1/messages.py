"""
消息通知API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


# 模拟消息存储（实际应该用数据库）
MESSAGES = []


@router.get("", summary="获取消息列表")
async def get_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_filter: Optional[int] = Query(None, description="消息类型：1系统通知，2预约提醒，3收藏更新"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的消息列表"""
    # 筛选当前用户的消息
    user_messages = [m for m in MESSAGES if m.get('user_id') == current_user.id]
    
    if type_filter:
        user_messages = [m for m in user_messages if m.get('type') == type_filter]
    
    # 按时间倒序
    user_messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    total = len(user_messages)
    start = (page - 1) * page_size
    end = start + page_size
    page_messages = user_messages[start:end]
    
    return {
        "list": page_messages,
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": len([m for m in user_messages if not m.get('is_read')])
    }


@router.get("/unread-count", summary="获取未读消息数")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取未读消息数量"""
    user_messages = [m for m in MESSAGES if m.get('user_id') == current_user.id and not m.get('is_read')]
    return {"unread_count": len(user_messages)}


@router.post("/{message_id}/read", summary="标记消息为已读")
async def mark_as_read(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记指定消息为已读"""
    for m in MESSAGES:
        if m.get('id') == message_id and m.get('user_id') == current_user.id:
            m['is_read'] = True
            return {"message": "标记成功"}
    
    raise HTTPException(status_code=404, detail="消息不存在")


@router.post("/read-all", summary="全部标记已读")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记所有消息为已读"""
    for m in MESSAGES:
        if m.get('user_id') == current_user.id:
            m['is_read'] = True
    
    return {"message": "全部已读"}


# 发送消息的函数（供其他模块调用）
def send_message(user_id: int, title: str, content: str, type: int = 1, related_id: int = None):
    """发送消息给用户"""
    message = {
        "id": len(MESSAGES) + 1,
        "user_id": user_id,
        "title": title,
        "content": content,
        "type": type,
        "related_id": related_id,
        "is_read": False,
        "created_at": datetime.now().isoformat()
    }
    MESSAGES.append(message)
    return message
