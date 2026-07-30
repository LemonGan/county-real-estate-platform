"""后台角色、经纪人和房源审核接口。"""
from datetime import datetime, timezone
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user
from app.api.v1.messages import create_message
from app.core.database import get_db
from app.core.permissions import Role, get_user_roles, require_roles
from app.models.audit_log import AuditLog
from app.models.feedback import Feedback
from app.models.property import Property
from app.models.property_review import PropertyReview
from app.models.short_video import ShortVideo
from app.models.video_interaction import VideoComment
from app.models.user import User

router = APIRouter()


class RoleUpdateRequest(BaseModel):
    roles: List[Role]


class PropertyReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    note: str | None = Field(default=None, max_length=500)


class PropertyReviewModerationRequest(BaseModel):
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
        "property_id", "previous_verification", "current_verification",
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
    response = {
        "property_id": property.id,
        "audit_status": property.audit_status,
        "status": property.status,
        "message": "审核完成",
    }
    property_title = property.title
    agent_id = property.agent_id
    review_note = property.audit_review_note
    await db.commit()
    try:
        if request.action == "approve":
            await create_message(
                db,
                agent_id,
                "房源审核通过",
                f"“{property_title}”已通过审核，现已公开展示。",
                message_type=3,
                related_id=property_id,
                related_type="property",
            )
        else:
            reason = f"审核说明：{review_note}" if review_note else "请完善房源信息后重新提交审核。"
            await create_message(
                db,
                agent_id,
                "房源审核未通过",
                f"“{property_title}”未通过审核，{reason}",
                message_type=3,
                related_id=property_id,
                related_type="property",
            )
    except Exception:
        # 通知属于附属能力，不能影响已经成功提交的审核决定。
        await db.rollback()
    return response


@router.get("/property-reviews/pending", summary="获取待审核房源评价")
async def list_pending_property_reviews(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(PropertyReview)
        .where(PropertyReview.status == 1, PropertyReview.is_verified == 0)
        .order_by(PropertyReview.created_at.asc(), PropertyReview.id.asc())
        .limit(limit)
        .options(selectinload(PropertyReview.property), selectinload(PropertyReview.user))
    )
    reviews = result.scalars().all()
    return {
        "items": [
            {
                "review_id": review.id,
                "property_id": review.property_id,
                "property_title": review.property.title if review.property else "已删除房源",
                "user_id": review.user_id,
                "user_nickname": (review.user.nickname or "用户") if review.user else "用户",
                "rating": review.rating,
                "content": review.content or "",
                "image_urls": review.images.split(",") if review.images else [],
                "submitted_at": review.created_at,
            }
            for review in reviews
        ],
        "total": len(reviews),
    }


@router.post("/property-reviews/{review_id}/review", summary="审核房源评价")
async def moderate_property_review(
    review_id: int,
    request: PropertyReviewModerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(PropertyReview)
        .where(PropertyReview.id == review_id)
        .options(selectinload(PropertyReview.property))
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价不存在")
    if review.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能审核自己的评价")
    if review.status != 1 or review.is_verified != 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该评价当前不在待审核状态")

    review.is_verified = 1 if request.action == "approve" else 2
    if request.action == "reject":
        review.status = 0
    review.reviewed_at = datetime.now(timezone.utc)
    review.reviewed_by = current_user.id
    review.review_note = request.note.strip() if request.note else None
    db.add(AuditLog(
        actor_id=current_user.id,
        action=f"property_review_moderation.{request.action}",
        target_type="property_review",
        target_id=str(review.id),
        details={
            "property_id": review.property_id,
            "previous_verification": 0,
            "current_verification": review.is_verified,
            "current_status": review.status,
        },
    ))
    response = {
        "review_id": review.id,
        "property_id": review.property_id,
        "is_verified": review.is_verified,
        "status": review.status,
        "message": "审核完成",
    }
    author_id = review.user_id
    property_id = review.property_id
    property_title = review.property.title if review.property else "该房源"
    review_note = review.review_note
    await db.commit()
    try:
        if request.action == "approve":
            await create_message(
                db, author_id, "房源评价已通过",
                f"您对“{property_title}”的评价已审核通过，现已公开展示。",
                message_type=1, related_id=property_id, related_type="property_review",
            )
        else:
            reason = f"审核说明：{review_note}" if review_note else "请调整内容后重新提交。"
            await create_message(
                db, author_id, "房源评价未通过",
                f"您对“{property_title}”的评价未通过审核，{reason}",
                message_type=1, related_id=property_id, related_type="property_review",
            )
    except Exception:
        await db.rollback()
    return response


class VideoCommentModerationRequest(BaseModel):
    action: Literal["approve", "reject"]
    note: str | None = Field(default=None, max_length=500)


@router.get("/video-comments/pending", summary="获取待审核短视频评论")
async def list_pending_video_comments(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(VideoComment)
        .where(VideoComment.status == 0, VideoComment.deleted_at.is_(None))
        .order_by(VideoComment.created_at.asc(), VideoComment.id.asc())
        .limit(limit)
        .options(selectinload(VideoComment.video), selectinload(VideoComment.user))
    )
    comments = result.scalars().all()
    return {"items": [
        {
            "comment_id": comment.id,
            "video_id": comment.video_id,
            "video_title": comment.video.title if comment.video else "已删除视频",
            "user_id": comment.user_id,
            "user_nickname": (comment.user.nickname or "用户") if comment.user else "用户",
            "content": comment.content,
            "submitted_at": comment.created_at,
        }
        for comment in comments
    ], "total": len(comments)}


@router.post("/video-comments/{comment_id}/review", summary="审核短视频评论")
async def moderate_video_comment(
    comment_id: int,
    request: VideoCommentModerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(VideoComment).where(VideoComment.id == comment_id).options(selectinload(VideoComment.video))
    )
    comment = result.scalar_one_or_none()
    if not comment or comment.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    if comment.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能审核自己的评论")
    if comment.status != 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该评论当前不在待审核状态")

    comment.status = 1 if request.action == "approve" else 2
    comment.reviewed_at = datetime.now(timezone.utc)
    comment.reviewed_by = current_user.id
    comment.review_note = request.note.strip() if request.note else None
    if request.action == "approve" and comment.video:
        comment.video.comment_count = (comment.video.comment_count or 0) + 1
    db.add(AuditLog(
        actor_id=current_user.id,
        action=f"video_comment_moderation.{request.action}",
        target_type="video_comment",
        target_id=str(comment.id),
        details={"video_id": comment.video_id, "previous_status": 0, "current_status": comment.status},
    ))
    response = {"comment_id": comment.id, "status": comment.status, "message": "审核完成"}
    author_id, video_id = comment.user_id, comment.video_id
    video_title = comment.video.title if comment.video else "该短视频"
    note = comment.review_note
    await db.commit()
    try:
        if request.action == "approve":
            await create_message(db, author_id, "短视频评论已通过", f"您在“{video_title}”下的评论已审核通过并公开展示。", message_type=1, related_id=video_id, related_type="short_video")
        else:
            reason = f"审核说明：{note}" if note else "请调整内容后重新提交。"
            await create_message(db, author_id, "短视频评论未通过", f"您在“{video_title}”下的评论未通过审核，{reason}", message_type=1, related_id=video_id, related_type="short_video")
    except Exception:
        await db.rollback()
    return response


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
    response = {"feedback_id": feedback.id, "status": feedback.status, "message": "处理状态已更新"}
    feedback_user_id = feedback.user_id
    feedback_status = feedback.status
    feedback_response = feedback.admin_response
    await db.commit()
    if feedback_user_id and (previous_status != feedback_status or feedback_response):
        status_text = {
            "processing": "已受理，正在处理中",
            "resolved": "已处理完成",
            "closed": "已关闭",
        }[feedback_status]
        content = f"您提交的反馈{status_text}。"
        if feedback_response:
            content += f" 回复：{feedback_response}"
        try:
            await create_message(
                db,
                feedback_user_id,
                "反馈处理进度更新",
                content,
                message_type=1,
                related_id=feedback.id,
                related_type="feedback",
            )
        except Exception:
            # 通知属于附属能力，不能影响已成功提交的反馈处理状态。
            await db.rollback()
    return response
