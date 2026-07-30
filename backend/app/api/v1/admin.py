"""后台角色、经纪人和房源审核接口。"""
from datetime import datetime, timezone
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.permissions import Role, get_user_roles, require_roles
from app.models.audit_log import AuditLog
from app.models.feedback import Feedback
from app.models.property import Property
from app.models.user import User

router = APIRouter()


class RoleUpdateRequest(BaseModel):
    roles: List[Role]


class PropertyReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    note: str | None = Field(default=None, max_length=500)


def _mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    if len(phone) <= 7:
        return "*" * len(phone)
    return f"{phone[:3]}****{phone[-4:]}"


@router.get("/users", summary="获取后台角色管理用户列表")
async def list_users_for_role_management(
    keyword: str | None = Query(default=None, min_length=1, max_length=50),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.SUPERADMIN)),
):
    query = select(User)
    if keyword:
        filters = [User.nickname.ilike(f"%{keyword.strip()}%")]
        if keyword.strip().isdigit():
            filters.append(User.id == int(keyword.strip()))
        query = query.where(or_(*filters))

    result = await db.execute(query.order_by(User.id.desc()).limit(limit))
    users = result.scalars().all()
    return {
        "items": [
            {
                "user_id": user.id,
                "nickname": user.nickname,
                "phone": _mask_phone(user.phone),
                "roles": sorted(get_user_roles(user)),
                "is_agent": user.is_agent,
                "agent_application_status": user.agent_application_status,
            }
            for user in users
        ],
        "total": len(users),
    }


@router.put("/users/{user_id}/roles", summary="更新后台角色")
async def update_user_roles(
    user_id: int,
    request: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.SUPERADMIN)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if target_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="超级管理员角色只能通过服务器维护")

    allowed_roles = {Role.REVIEWER.value, Role.OPERATIONS.value, Role.ADMIN.value}
    requested_roles = {role.value for role in request.roles if role.value in allowed_roles}
    old_roles = get_user_roles(target_user)
    if target_user.is_agent and target_user.agent_application_status == "approved":
        requested_roles.add(Role.AGENT.value)
    target_user.roles = sorted(requested_roles) or [Role.USER.value]
    db.add(AuditLog(
        actor_id=current_user.id,
        action="roles.updated",
        target_type="user",
        target_id=str(target_user.id),
        details={"before": sorted(old_roles), "after": target_user.roles},
    ))
    await db.commit()
    return {"user_id": target_user.id, "roles": target_user.roles}


@router.get("/audit-logs", summary="获取后台审核记录")
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(AuditLog, User.nickname)
        .outerjoin(User, AuditLog.actor_id == User.id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(limit)
    )
    allowed_detail_keys = {
        "before", "after", "roles",
        "previous_status", "current_status",
        "previous_audit_status", "current_audit_status", "current_status",
    }
    items = []
    for audit_log, actor_nickname in result.all():
        raw_details = audit_log.details if isinstance(audit_log.details, dict) else {}
        details = {key: raw_details[key] for key in allowed_detail_keys if key in raw_details}
        items.append({
            "id": audit_log.id,
            "action": audit_log.action,
            "target_type": audit_log.target_type,
            "target_id": audit_log.target_id,
            "actor": actor_nickname or (f"管理员 #{audit_log.actor_id}" if audit_log.actor_id else "系统"),
            "details": details,
            "created_at": audit_log.created_at,
        })
    return {"items": items, "total": len(items)}


@router.get("/properties/pending", summary="获取待审核房源")
async def list_pending_properties(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(Property)
        .where(Property.deleted_at.is_(None), Property.audit_status == 0)
        .order_by(Property.created_at.asc(), Property.id.asc())
        .limit(limit)
        .options(selectinload(Property.agent), selectinload(Property.images))
    )
    properties = result.scalars().all()
    return {
        "items": [
            {
                "property_id": property.id,
                "title": property.title,
                "total_price": property.total_price,
                "area": float(property.area) if property.area is not None else None,
                "location": " ".join(filter(None, [property.province, property.city, property.district, property.town, property.detail_address])),
                "cover_url": property.cover_url,
                "image_urls": [image.image_url for image in property.images],
                "agent_id": property.agent_id,
                "agent_name": (property.agent.nickname or property.agent.real_name) if property.agent else None,
                "agent_phone": _mask_phone(property.agent.phone) if property.agent else None,
                "submitted_at": property.created_at,
            }
            for property in properties
        ],
        "total": len(properties),
    }


@router.post("/properties/{property_id}/review", summary="审核房源")
async def review_property(
    property_id: int,
    request: PropertyReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(select(Property).where(Property.id == property_id, Property.deleted_at.is_(None)))
    property = result.scalar_one_or_none()
    if not property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源不存在")
    if property.agent_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能审核自己发布的房源")
    if property.audit_status != 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该房源当前不在待审核状态")

    if request.action == "approve":
        property.audit_status = 1
        property.status = 1
    else:
        property.audit_status = 2
        property.status = 3
    property.audit_reviewed_at = datetime.now(timezone.utc)
    property.audit_reviewed_by = current_user.id
    property.audit_review_note = request.note.strip() if request.note else None
    db.add(AuditLog(
        actor_id=current_user.id,
        action=f"property_review.{request.action}",
        target_type="property",
        target_id=str(property.id),
        details={
            "previous_audit_status": 0,
            "current_audit_status": property.audit_status,
            "current_status": property.status,
        },
    ))
    await db.commit()
    return {
        "property_id": property.id,
        "audit_status": property.audit_status,
        "status": property.status,
        "message": "审核完成",
    }



class FeedbackStatusUpdateRequest(BaseModel):
    status: Literal["processing", "resolved", "closed"]
    response: str | None = Field(default=None, max_length=500)


@router.get("/feedback", summary="获取待处理用户反馈")
async def list_feedback(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(Feedback, User.nickname)
        .outerjoin(User, Feedback.user_id == User.id)
        .where(Feedback.status.in_(["pending", "processing"]))
        .order_by(Feedback.created_at.asc(), Feedback.id.asc())
        .limit(limit)
    )
    items = []
    for feedback, nickname in result.all():
        items.append({
            "feedback_id": feedback.id,
            "category": feedback.category,
            "content": feedback.content,
            "status": feedback.status,
            "nickname": nickname or "用户",
            "created_at": feedback.created_at,
        })
    return {"items": items, "total": len(items)}


@router.post("/feedback/{feedback_id}/status", summary="更新用户反馈处理状态")
async def update_feedback_status(
    feedback_id: int,
    request: FeedbackStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="反馈不存在")
    previous_status = feedback.status
    feedback.status = request.status
    feedback.admin_response = request.response.strip() if request.response else None
    feedback.handled_by = current_user.id
    feedback.handled_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        actor_id=current_user.id,
        action="feedback.status_updated",
        target_type="feedback",
        target_id=str(feedback.id),
        details={"previous_status": previous_status, "current_status": feedback.status},
    ))
    await db.commit()
    return {"feedback_id": feedback.id, "status": feedback.status, "message": "处理状态已更新"}
