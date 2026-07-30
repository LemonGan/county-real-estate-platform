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
