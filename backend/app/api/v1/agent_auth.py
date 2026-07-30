"""经纪人认证申请与后台审核接口。"""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.permissions import Role, get_user_roles, require_roles
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


class AgentApplyRequest(BaseModel):
    real_name: str = Field(min_length=1, max_length=50)
    id_card: str = Field(min_length=18, max_length=18)
    agent_license: str = Field(min_length=1, max_length=50)
    company: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=11, max_length=20)


class AgentReviewRequest(BaseModel):
    action: Literal["approve", "reject", "suspend"]
    note: str | None = Field(default=None, max_length=500)


def _mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    if len(phone) <= 7:
        return "*" * len(phone)
    return f"{phone[:3]}****{phone[-4:]}"


def _mask_id_card(id_card: str | None) -> str | None:
    if not id_card:
        return None
    if len(id_card) <= 8:
        return "*" * len(id_card)
    return f"{id_card[:4]}**********{id_card[-4:]}"


def _stored_roles(user: User) -> set[str]:
    return {str(role) for role in user.roles} if isinstance(user.roles, list) else set()


def _set_agent_role(user: User, enabled: bool) -> None:
    roles = _stored_roles(user)
    if enabled:
        roles.add(Role.AGENT.value)
    else:
        roles.discard(Role.AGENT.value)
    user.roles = sorted(roles) or [Role.USER.value]


@router.post("/apply", summary="申请成为经纪人")
async def apply_as_agent(
    request: AgentApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.agent_application_status == "approved" or current_user.is_agent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="您已经是经纪人了")
    if current_user.agent_application_status == "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="您的申请正在审核中，请勿重复提交")

    current_user.real_name = request.real_name.strip()
    current_user.id_card = request.id_card.strip().upper()
    current_user.agent_license = request.agent_license.strip()
    current_user.agent_company = request.company.strip()
    current_user.phone = request.phone.strip()
    current_user.is_agent = False
    current_user.is_verified = False
    current_user.agent_application_status = "pending"
    current_user.agent_application_submitted_at = datetime.now(timezone.utc)
    current_user.agent_reviewed_at = None
    current_user.agent_reviewed_by = None
    current_user.agent_review_note = None
    _set_agent_role(current_user, enabled=False)

    await db.commit()
    return {
        "user_id": current_user.id,
        "status": "pending",
        "message": "申请已提交，等待后台审核",
    }


@router.get("/applications", summary="获取待审核经纪人申请")
async def list_agent_applications(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    result = await db.execute(
        select(User)
        .where(User.agent_application_status == "pending")
        .order_by(User.agent_application_submitted_at.asc(), User.id.asc())
        .limit(limit)
    )
    applications = result.scalars().all()
    return {
        "items": [
            {
                "user_id": user.id,
                "real_name": user.real_name,
                "phone": _mask_phone(user.phone),
                "id_card": _mask_id_card(user.id_card),
                "agent_license": user.agent_license,
                "company": user.agent_company,
                "status": user.agent_application_status,
                "submitted_at": user.agent_application_submitted_at,
            }
            for user in applications
        ],
        "total": len(applications),
    }


@router.post("/applications/{user_id}/review", summary="审核经纪人申请")
async def review_agent_application(
    user_id: int,
    request: AgentReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.REVIEWER, Role.ADMIN, Role.SUPERADMIN)),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能审核自己的经纪人申请")

    result = await db.execute(select(User).where(User.id == user_id))
    applicant = result.scalar_one_or_none()
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    previous_status = applicant.agent_application_status
    if request.action in {"approve", "reject"} and previous_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该申请当前不在待审核状态")
    if request.action == "suspend" and previous_status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能停用已通过的经纪人")

    if request.action == "approve":
        applicant.is_agent = True
        applicant.is_verified = True
        applicant.agent_application_status = "approved"
        _set_agent_role(applicant, enabled=True)
    else:
        applicant.is_agent = False
        applicant.is_verified = False
        applicant.agent_application_status = "rejected" if request.action == "reject" else "suspended"
        _set_agent_role(applicant, enabled=False)

    applicant.agent_reviewed_at = datetime.now(timezone.utc)
    applicant.agent_reviewed_by = current_user.id
    applicant.agent_review_note = request.note.strip() if request.note else None
    db.add(AuditLog(
        actor_id=current_user.id,
        action=f"agent_application.{request.action}",
        target_type="user",
        target_id=str(applicant.id),
        details={
            "previous_status": previous_status,
            "current_status": applicant.agent_application_status,
            "roles": sorted(get_user_roles(applicant)),
        },
    ))
    await db.commit()
    return {
        "user_id": applicant.id,
        "status": applicant.agent_application_status,
        "is_agent": applicant.is_agent,
        "message": "审核完成",
    }


@router.get("/status", summary="获取经纪人状态")
async def get_agent_status(
    current_user: User = Depends(get_current_active_user),
):
    return {
        "is_agent": current_user.is_agent,
        "is_verified": current_user.is_verified,
        "application_status": current_user.agent_application_status,
        "real_name": current_user.real_name,
        "agent_license": current_user.agent_license,
        "company": current_user.agent_company,
        "submitted_at": current_user.agent_application_submitted_at,
        "reviewed_at": current_user.agent_reviewed_at,
        "review_note": current_user.agent_review_note,
    }
