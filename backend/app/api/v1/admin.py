"""后台角色、经纪人和房源审核接口。"""
from datetime import datetime, timezone
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user
from app.api.v1.messages import create_message
from app.core.database import get_db
from app.core.permissions import Role, build_permission_policy_payload, get_user_roles, require_roles
from app.models.audit_log import AuditLog
from app.models.appointment import Appointment
from app.models.feedback import Feedback
from app.models.news_article import NewsArticle
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


class NewsArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=500)
    content: str = Field(..., min_length=1)
    cover_url: str | None = Field(default=None, max_length=1000)
    category: str = Field(..., min_length=1, max_length=50)
    category_name: str | None = Field(default=None, max_length=50)
    tags: List[str] | None = None
    author_name: str | None = Field(default=None, max_length=50)
    author_avatar: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=0, le=9999)
    is_published: bool = False


class NewsArticleUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None)
    cover_url: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    category_name: str | None = Field(default=None, max_length=50)
    tags: List[str] | None = None
    author_name: str | None = Field(default=None, max_length=50)
    author_avatar: str | None = Field(default=None, max_length=500)
    sort_order: int | None = Field(default=None, ge=0, le=9999)
    is_published: bool | None = None


def _mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    if len(phone) <= 7:
        return "*" * len(phone)
    return f"{phone[:3]}****{phone[-4:]}"


def _mask_contact(contact: str | None) -> str | None:
    if not contact:
        return None
    value = contact.strip()
    if not value:
        return None
    if "@" in value:
        name, _, domain = value.partition("@")
        if not domain:
            return "***"
        prefix = name[:2] if len(name) > 2 else name[:1]
        return f"{prefix}***@{domain}"
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) >= 7:
        return _mask_phone(digits)
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def _serialize_admin_feedback(feedback: Feedback, nickname: str | None = None, phone: str | None = None) -> dict:
    return {
        "feedback_id": feedback.id,
        "user_id": feedback.user_id,
        "category": feedback.category,
        "content": feedback.content,
        "contact": _mask_contact(feedback.contact),
        "source": feedback.source,
        "status": feedback.status,
        "admin_response": feedback.admin_response,
        "handled_by": feedback.handled_by,
        "handled_at": feedback.handled_at,
        "nickname": nickname or "用户",
        "phone": _mask_phone(phone),
        "created_at": feedback.created_at,
        "updated_at": feedback.updated_at,
    }


def _normalize_html_content(content: str) -> str:
    content = content.strip()
    if not content:
        return content
    if "<" in content and ">" in content:
        return content
    paragraphs = [part.strip() for part in content.splitlines() if part.strip()]
    if not paragraphs:
        return ""
    return "".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)


def _serialize_news(article: NewsArticle) -> dict:
    author_name = article.author_name or (article.author.nickname if article.author and article.author.nickname else None) or "未命名作者"
    author_avatar = article.author_avatar or (article.author.avatar if article.author and article.author.avatar else "")
    return {
        "id": article.id,
        "title": article.title,
        "summary": article.summary or "",
        "content": article.content,
        "cover_url": article.cover_url or "",
        "category": article.category,
        "category_name": article.category_name or article.category,
        "tags": article.tags or [],
        "author_id": article.author_id,
        "author_name": author_name,
        "author_avatar": author_avatar,
        "is_published": article.is_published,
        "publish_time": article.publish_time,
        "sort_order": article.sort_order or 0,
        "view_count": article.view_count or 0,
        "like_count": article.like_count or 0,
        "collect_count": article.collect_count or 0,
        "share_count": article.share_count or 0,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }


@router.get("/permissions", summary="获取后台权限规则")
async def get_permission_policy(
    current_user: User = Depends(get_current_active_user),
):
    return build_permission_policy_payload(current_user)


@router.get("/dashboard", summary="获取后台数据看板")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    async def count_from(model, *conditions):
        result = await db.execute(select(func.count()).select_from(model).where(*conditions))
        return result.scalar_one() or 0

    async def sum_news_field(field):
        result = await db.execute(select(func.coalesce(func.sum(field), 0)).select_from(NewsArticle).where(NewsArticle.deleted_at.is_(None)))
        return int(result.scalar_one() or 0)

    pending_agent_applications = await count_from(User, User.deleted_at.is_(None), User.agent_application_status == "pending")
    pending_properties = await count_from(Property, Property.deleted_at.is_(None), Property.audit_status == 0)
    pending_property_reviews = await count_from(PropertyReview, PropertyReview.status == 1, PropertyReview.is_verified == 0)
    pending_video_comments = await count_from(VideoComment, VideoComment.deleted_at.is_(None), VideoComment.status == 0)
    active_feedback = await count_from(Feedback, Feedback.status.in_(["pending", "processing"]))

    total_users = await count_from(User, User.deleted_at.is_(None))
    approved_agents = await count_from(User, User.deleted_at.is_(None), User.is_agent.is_(True), User.agent_application_status == "approved")
    total_properties = await count_from(Property, Property.deleted_at.is_(None))
    published_properties = await count_from(Property, Property.deleted_at.is_(None), Property.audit_status == 1, Property.status == 1)
    total_appointments = await count_from(Appointment, Appointment.deleted_at.is_(None))
    pending_appointments = await count_from(Appointment, Appointment.deleted_at.is_(None), Appointment.status == 1)
    total_news = await count_from(NewsArticle, NewsArticle.deleted_at.is_(None))
    published_news = await count_from(NewsArticle, NewsArticle.deleted_at.is_(None), NewsArticle.is_published.is_(True))
    draft_news = await count_from(NewsArticle, NewsArticle.deleted_at.is_(None), NewsArticle.is_published.is_(False))
    total_feedback = await count_from(Feedback)
    resolved_feedback = await count_from(Feedback, Feedback.status == "resolved")
    audit_logs = await count_from(AuditLog)

    pending_total = pending_agent_applications + pending_properties + pending_property_reviews + pending_video_comments + active_feedback + pending_appointments

    return {
        "pending": {
            "total": pending_total,
            "agent_applications": pending_agent_applications,
            "properties": pending_properties,
            "property_reviews": pending_property_reviews,
            "video_comments": pending_video_comments,
            "feedback": active_feedback,
            "appointments": pending_appointments,
        },
        "users": {"total": total_users, "approved_agents": approved_agents},
        "properties": {"total": total_properties, "published": published_properties, "pending": pending_properties},
        "appointments": {"total": total_appointments, "pending": pending_appointments},
        "news": {
            "total": total_news,
            "published": published_news,
            "draft": draft_news,
            "views": await sum_news_field(NewsArticle.view_count),
            "likes": await sum_news_field(NewsArticle.like_count),
            "collects": await sum_news_field(NewsArticle.collect_count),
        },
        "feedback": {"total": total_feedback, "active": active_feedback, "resolved": resolved_feedback},
        "audit": {"total": audit_logs},
        "generated_at": datetime.now(timezone.utc),
    }


@router.get("/users", summary="获取后台角色管理用户列表")
async def list_users_for_role_management(
    keyword: str | None = Query(default=None, min_length=1, max_length=50),
    role: str = Query(default="all", max_length=30),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    limit: int | None = Query(default=None, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.SUPERADMIN)),
):
    allowed_role_filters = {"all", Role.USER.value, Role.AGENT.value, Role.REVIEWER.value, Role.OPERATIONS.value, Role.ADMIN.value, Role.SUPERADMIN.value}
    if role not in allowed_role_filters:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="成员角色筛选参数无效")

    conditions = [User.deleted_at.is_(None)]
    if keyword:
        keyword_value = keyword.strip()
        filters = [User.nickname.ilike(f"%{keyword_value}%"), User.phone.ilike(f"%{keyword_value}%")]
        if keyword_value.isdigit():
            filters.append(User.id == int(keyword_value))
        conditions.append(or_(*filters))

    result = await db.execute(select(User).where(*conditions).order_by(User.id.desc()))
    all_users = result.scalars().all()
    filtered_users = [user for user in all_users if role == "all" or role in get_user_roles(user)]
    total = len(filtered_users)
    effective_page_size = limit or page_size
    offset = (page - 1) * effective_page_size
    users = filtered_users[offset:offset + effective_page_size]
    return {
        "items": [
            {
                "user_id": user.id,
                "nickname": user.nickname,
                "phone": _mask_phone(user.phone),
                "roles": sorted(get_user_roles(user)),
                "is_agent": user.is_agent,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "agent_application_status": user.agent_application_status,
                "agent_company": user.agent_company,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at,
            }
            for user in users
        ],
        "total": total,
        "page": page,
        "page_size": effective_page_size,
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


def _parse_date_filter(value: str | None, end_of_day: bool = False) -> datetime | None:
    if not value:
        return None
    raw_value = value.strip()
    if not raw_value:
        return None
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期参数格式无效")
    if len(raw_value) == 10:
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999) if end_of_day else parsed.replace(hour=0, minute=0, second=0, microsecond=0)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@router.get("/audit-logs", summary="获取后台操作记录")
async def list_audit_logs(
    action: str | None = Query(default=None, max_length=80),
    target_type: str | None = Query(default=None, max_length=50),
    keyword: str | None = Query(default=None, max_length=80),
    date_from: str | None = Query(default=None, max_length=30),
    date_to: str | None = Query(default=None, max_length=30),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.SUPERADMIN)),
):
    conditions = []
    if action and action != "all":
        conditions.append(AuditLog.action == action)
    if target_type and target_type != "all":
        conditions.append(AuditLog.target_type == target_type)

    keyword_value = keyword.strip() if keyword else ""
    if keyword_value:
        like_value = f"%{keyword_value}%"
        conditions.append(or_(
            AuditLog.action.like(like_value),
            AuditLog.target_type.like(like_value),
            AuditLog.target_id.like(like_value),
            User.nickname.like(like_value),
            User.phone.like(like_value),
        ))

    start_at = _parse_date_filter(date_from)
    end_at = _parse_date_filter(date_to, end_of_day=True)
    if start_at:
        conditions.append(AuditLog.created_at >= start_at)
    if end_at:
        conditions.append(AuditLog.created_at <= end_at)

    total_result = await db.execute(
        select(func.count())
        .select_from(AuditLog)
        .outerjoin(User, AuditLog.actor_id == User.id)
        .where(*conditions)
    )
    total = total_result.scalar_one() or 0
    result = await db.execute(
        select(AuditLog, User.nickname, User.phone)
        .outerjoin(User, AuditLog.actor_id == User.id)
        .where(*conditions)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    allowed_detail_keys = {
        "before", "after", "roles",
        "previous_status", "current_status",
        "previous_audit_status", "current_audit_status",
        "property_id", "previous_verification", "current_verification",
        "title", "is_published", "publish_time",
    }
    items = []
    for audit_log, actor_nickname, actor_phone in result.all():
        raw_details = audit_log.details if isinstance(audit_log.details, dict) else {}
        details = {key: raw_details[key] for key in allowed_detail_keys if key in raw_details}
        actor = actor_nickname or (f"管理员 #{audit_log.actor_id}" if audit_log.actor_id else "系统")
        items.append({
            "id": audit_log.id,
            "action": audit_log.action,
            "target_type": audit_log.target_type,
            "target_id": audit_log.target_id,
            "actor_id": audit_log.actor_id,
            "actor": actor,
            "actor_phone": _mask_phone(actor_phone),
            "details": details,
            "created_at": audit_log.created_at,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


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


@router.get("/news", summary="获取后台资讯列表")
async def list_news_articles(
    limit: int | None = Query(default=None, ge=1, le=100),
    publish_status: str = Query(default="all", max_length=20),
    category: str | None = Query(default=None, max_length=50),
    keyword: str | None = Query(default=None, max_length=80),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    allowed_publish_status = {"all", "published", "draft"}
    if publish_status not in allowed_publish_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资讯发布状态参数无效")

    conditions = [NewsArticle.deleted_at.is_(None)]
    if publish_status == "published":
        conditions.append(NewsArticle.is_published.is_(True))
    elif publish_status == "draft":
        conditions.append(NewsArticle.is_published.is_(False))

    if category and category != "all":
        conditions.append(NewsArticle.category == category)

    keyword_value = keyword.strip() if keyword else ""
    if keyword_value:
        like_value = f"%{keyword_value}%"
        conditions.append(or_(
            NewsArticle.title.like(like_value),
            NewsArticle.summary.like(like_value),
            NewsArticle.category_name.like(like_value),
            NewsArticle.author_name.like(like_value),
        ))

    total_result = await db.execute(select(func.count()).select_from(NewsArticle).where(*conditions))
    total = total_result.scalar_one() or 0
    effective_page_size = limit or page_size
    result = await db.execute(
        select(NewsArticle)
        .where(*conditions)
        .order_by(NewsArticle.sort_order.desc(), NewsArticle.publish_time.desc(), NewsArticle.id.desc())
        .offset((page - 1) * effective_page_size)
        .limit(effective_page_size)
        .options(selectinload(NewsArticle.author))
    )
    articles = result.scalars().all()
    return {"items": [_serialize_news(article) for article in articles], "total": total, "page": page, "page_size": effective_page_size}


@router.post("/news", summary="创建资讯")
async def create_news_article(
    request: NewsArticleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    article = NewsArticle(
        title=request.title.strip(),
        summary=request.summary.strip() if request.summary else None,
        content=_normalize_html_content(request.content),
        cover_url=request.cover_url.strip() if request.cover_url else None,
        category=request.category.strip(),
        category_name=request.category_name.strip() if request.category_name else None,
        tags=request.tags or [],
        author_id=current_user.id,
        author_name=request.author_name.strip() if request.author_name else (current_user.nickname or current_user.real_name or current_user.phone),
        author_avatar=request.author_avatar.strip() if request.author_avatar else (current_user.avatar or None),
        sort_order=request.sort_order,
        is_published=request.is_published,
        publish_time=datetime.now(timezone.utc) if request.is_published else None,
    )
    db.add(article)
    await db.flush()
    db.add(AuditLog(
        actor_id=current_user.id,
        action="news.created",
        target_type="news",
        target_id=str(article.id),
        details={"title": article.title, "is_published": article.is_published},
    ))
    await db.commit()
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article.id).options(selectinload(NewsArticle.author)))
    return _serialize_news(result.scalar_one())


@router.put("/news/{news_id}", summary="更新资讯")
async def update_news_article(
    news_id: int,
    request: NewsArticleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == news_id, NewsArticle.deleted_at.is_(None)).options(selectinload(NewsArticle.author)))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资讯不存在")

    before = {
        "title": article.title,
        "category": article.category,
        "is_published": article.is_published,
        "sort_order": article.sort_order,
    }
    if request.title is not None:
        article.title = request.title.strip()
    if request.summary is not None:
        article.summary = request.summary.strip() if request.summary else None
    if request.content is not None:
        article.content = _normalize_html_content(request.content)
    if request.cover_url is not None:
        article.cover_url = request.cover_url.strip() if request.cover_url else None
    if request.category is not None:
        article.category = request.category.strip()
    if request.category_name is not None:
        article.category_name = request.category_name.strip() if request.category_name else None
    if request.tags is not None:
        article.tags = request.tags
    if request.author_name is not None:
        article.author_name = request.author_name.strip() if request.author_name else None
    if request.author_avatar is not None:
        article.author_avatar = request.author_avatar.strip() if request.author_avatar else None
    if request.sort_order is not None:
        article.sort_order = request.sort_order
    if request.is_published is not None:
        article.is_published = request.is_published
        article.publish_time = datetime.now(timezone.utc) if request.is_published and article.publish_time is None else article.publish_time
        if not request.is_published:
            article.publish_time = None
    db.add(AuditLog(
        actor_id=current_user.id,
        action="news.updated",
        target_type="news",
        target_id=str(article.id),
        details={"before": before, "after": {"title": article.title, "category": article.category, "is_published": article.is_published, "sort_order": article.sort_order}},
    ))
    await db.commit()
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article.id).options(selectinload(NewsArticle.author)))
    return _serialize_news(result.scalar_one())


@router.post("/news/{news_id}/publish", summary="发布资讯")
async def publish_news_article(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == news_id, NewsArticle.deleted_at.is_(None)).options(selectinload(NewsArticle.author)))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资讯不存在")
    article.is_published = True
    article.publish_time = datetime.now(timezone.utc)
    db.add(AuditLog(
        actor_id=current_user.id,
        action="news.published",
        target_type="news",
        target_id=str(article.id),
        details={"title": article.title, "publish_time": article.publish_time.isoformat() if article.publish_time else None},
    ))
    await db.commit()
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article.id).options(selectinload(NewsArticle.author)))
    return _serialize_news(result.scalar_one())


@router.delete("/news/{news_id}", summary="删除资讯")
async def delete_news_article(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == news_id, NewsArticle.deleted_at.is_(None)).options(selectinload(NewsArticle.author)))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资讯不存在")
    article.deleted_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        actor_id=current_user.id,
        action="news.deleted",
        target_type="news",
        target_id=str(article.id),
        details={"title": article.title},
    ))
    await db.commit()
    return {"news_id": news_id, "message": "资讯已删除"}


@router.get("/feedback", summary="获取用户反馈列表")
async def list_feedback(
    status_filter: str = Query(default="active", alias="status", max_length=20),
    category: str | None = Query(default=None, max_length=30),
    keyword: str | None = Query(default=None, max_length=80),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    allowed_status = {"active", "all", "pending", "processing", "resolved", "closed"}
    if status_filter not in allowed_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="反馈状态参数无效")

    conditions = []
    if status_filter == "active":
        conditions.append(Feedback.status.in_(["pending", "processing"]))
    elif status_filter != "all":
        conditions.append(Feedback.status == status_filter)

    if category and category != "all":
        conditions.append(Feedback.category == category)

    keyword_value = keyword.strip() if keyword else ""
    if keyword_value:
        like_value = f"%{keyword_value}%"
        conditions.append(or_(
            Feedback.content.like(like_value),
            Feedback.contact.like(like_value),
            User.nickname.like(like_value),
            User.phone.like(like_value),
        ))

    total_result = await db.execute(
        select(func.count())
        .select_from(Feedback)
        .outerjoin(User, Feedback.user_id == User.id)
        .where(*conditions)
    )
    total = total_result.scalar_one() or 0
    order_columns = (Feedback.created_at.asc(), Feedback.id.asc()) if status_filter in {"active", "pending", "processing"} else (Feedback.created_at.desc(), Feedback.id.desc())
    result = await db.execute(
        select(Feedback, User.nickname, User.phone)
        .outerjoin(User, Feedback.user_id == User.id)
        .where(*conditions)
        .order_by(*order_columns)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [_serialize_admin_feedback(feedback, nickname, phone) for feedback, nickname, phone in result.all()]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/feedback/{feedback_id}", summary="获取用户反馈详情")
async def get_feedback_detail(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.OPERATIONS, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(Feedback, User.nickname, User.phone)
        .outerjoin(User, Feedback.user_id == User.id)
        .where(Feedback.id == feedback_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="反馈不存在")
    feedback, nickname, phone = row
    return _serialize_admin_feedback(feedback, nickname, phone)


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
