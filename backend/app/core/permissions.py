"""后台角色与权限依赖。"""
from enum import Enum
from typing import Iterable, Set

from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_active_user
from app.models.user import User


class Role(str, Enum):
    USER = "user"
    AGENT = "agent"
    REVIEWER = "reviewer"
    OPERATIONS = "operations"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class Capability(str, Enum):
    REVIEW_AGENT_APPLICATIONS = "review_agent_applications"
    REVIEW_PROPERTIES = "review_properties"
    MODERATE_PROPERTY_REVIEWS = "moderate_property_reviews"
    MODERATE_VIDEO_COMMENTS = "moderate_video_comments"
    MANAGE_NEWS = "manage_news"
    MANAGE_FEEDBACK = "manage_feedback"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_ROLES = "manage_roles"


ROLE_POLICY = {
    Role.USER.value: {
        "label": "普通用户",
        "description": "小程序普通使用者，不进入后台管理台。",
        "capabilities": [],
    },
    Role.AGENT.value: {
        "label": "经纪人",
        "description": "通过认证后可维护自己的房源和客户工作台，不拥有后台审核权限。",
        "capabilities": [],
    },
    Role.REVIEWER.value: {
        "label": "审核员",
        "description": "处理经纪人申请、房源审核、评价审核和短视频评论审核。",
        "capabilities": [
            Capability.REVIEW_AGENT_APPLICATIONS.value,
            Capability.REVIEW_PROPERTIES.value,
            Capability.MODERATE_PROPERTY_REVIEWS.value,
            Capability.MODERATE_VIDEO_COMMENTS.value,
        ],
    },
    Role.OPERATIONS.value: {
        "label": "运营",
        "description": "维护资讯内容和用户反馈，不分配后台角色。",
        "capabilities": [
            Capability.MANAGE_NEWS.value,
            Capability.MANAGE_FEEDBACK.value,
        ],
    },
    Role.ADMIN.value: {
        "label": "管理员",
        "description": "具备审核、内容运营、反馈处理和审计查看权限，不分配后台角色。",
        "capabilities": [
            Capability.REVIEW_AGENT_APPLICATIONS.value,
            Capability.REVIEW_PROPERTIES.value,
            Capability.MODERATE_PROPERTY_REVIEWS.value,
            Capability.MODERATE_VIDEO_COMMENTS.value,
            Capability.MANAGE_NEWS.value,
            Capability.MANAGE_FEEDBACK.value,
            Capability.VIEW_AUDIT_LOGS.value,
        ],
    },
    Role.SUPERADMIN.value: {
        "label": "超级管理员",
        "description": "服务器维护角色，拥有所有后台权限，包括成员角色分配。",
        "capabilities": [capability.value for capability in Capability],
    },
}

CAPABILITY_LABELS = {
    Capability.REVIEW_AGENT_APPLICATIONS.value: "经纪人申请审核",
    Capability.REVIEW_PROPERTIES.value: "房源审核",
    Capability.MODERATE_PROPERTY_REVIEWS.value: "房源评价审核",
    Capability.MODERATE_VIDEO_COMMENTS.value: "短视频评论审核",
    Capability.MANAGE_NEWS.value: "资讯运营",
    Capability.MANAGE_FEEDBACK.value: "用户反馈处理",
    Capability.VIEW_AUDIT_LOGS.value: "操作记录查看",
    Capability.MANAGE_ROLES.value: "成员角色分配",
}


def get_user_roles(user: User) -> Set[str]:
    """兼容旧布尔字段，返回用户有效角色集合。"""
    stored_roles = user.roles if isinstance(user.roles, list) else []
    roles = {str(role) for role in stored_roles if role}
    if user.is_superuser:
        roles.add(Role.SUPERADMIN.value)
    if user.is_agent and user.agent_application_status == "approved":
        roles.add(Role.AGENT.value)
    if not roles:
        roles.add(Role.USER.value)
    return roles


def get_role_capabilities(roles: Iterable[str]) -> Set[str]:
    """根据角色集合返回可执行能力集合。"""
    capabilities: Set[str] = set()
    for role in roles:
        policy = ROLE_POLICY.get(str(role))
        if not policy:
            continue
        capabilities.update(str(capability) for capability in policy["capabilities"])
    return capabilities


def get_user_capabilities(user: User) -> Set[str]:
    """返回用户有效后台能力集合。"""
    return get_role_capabilities(get_user_roles(user))


def has_capability(user: User, capability: Capability | str) -> bool:
    """判断用户是否具备指定后台能力。"""
    return str(capability.value if isinstance(capability, Capability) else capability) in get_user_capabilities(user)


def build_permission_policy_payload(user: User) -> dict:
    """返回后台权限规则和当前用户能力，用于管理台展示。"""
    roles = sorted(get_user_roles(user))
    capabilities = sorted(get_user_capabilities(user))
    return {
        "current_user": {
            "user_id": user.id,
            "nickname": user.nickname or user.phone or f"用户 #{user.id}",
            "roles": roles,
            "role_labels": [ROLE_POLICY.get(role, {"label": role})["label"] for role in roles],
            "capabilities": capabilities,
            "capability_labels": [CAPABILITY_LABELS.get(capability, capability) for capability in capabilities],
        },
        "roles": [
            {
                "key": role,
                "label": policy["label"],
                "description": policy["description"],
                "capabilities": list(policy["capabilities"]),
                "capability_labels": [CAPABILITY_LABELS.get(capability, capability) for capability in policy["capabilities"]],
            }
            for role, policy in ROLE_POLICY.items()
        ],
        "capabilities": [
            {"key": capability, "label": label}
            for capability, label in CAPABILITY_LABELS.items()
        ],
    }


def require_roles(*required_roles: Role):
    allowed = {role.value for role in required_roles}

    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        roles = get_user_roles(current_user)
        if Role.SUPERADMIN.value in roles or roles.intersection(allowed):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前账号没有执行此操作的权限",
        )

    return dependency
