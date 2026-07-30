"""经纪人公开响应 Schema。"""
from typing import Optional

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """仅包含已审核经纪人的真实公开资料。"""

    id: int
    nickname: str
    avatar: Optional[str] = None
    avatar_url: Optional[str] = None
    company: Optional[str] = None
    sales_count: int = 0
    service_count: int = 0
    property_count: int = 0
    tags: list[str] = Field(default_factory=list)
    is_verified: bool = False

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    list: list[AgentResponse]
    total: int
    page: int
    page_size: int
