"""
经纪人相关Schema
"""
from pydantic import BaseModel


class AgentResponse(BaseModel):
    """经纪人响应"""
    id: int
    nickname: str
    avatar: str = None
    avatar_url: str = None
    phone: str = None
    company: str = None
    experience: int = 0
    rating: float = 0.0
    sales_count: int = 0
    service_count: int = 0
    introduction: str = None
    tags: list = []
    is_verified: bool = False

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """经纪人列表响应"""
    list: list[AgentResponse]
    total: int
    page: int
    page_size: int
