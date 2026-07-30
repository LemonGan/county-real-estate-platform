"""会员接口占位：付费能力审批完成前不得开通或兑换会员。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()
PAYMENT_FEATURE_MESSAGE = "会员付费与兑换功能暂未开放"


class MemberBuyRequest(BaseModel):
    level: int


class MemberExchangeRequest(BaseModel):
    code: str


class MemberStatusResponse(BaseModel):
    is_member: bool
    member_level: int
    member_expire: Optional[str]
    days_remaining: int
    available: bool = False


@router.get("/status", response_model=MemberStatusResponse, summary="获取会员状态")
async def get_member_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """仅保留历史状态只读查询；当前不提供任何付费权益。"""
    return {
        "is_member": False,
        "member_level": 0,
        "member_expire": None,
        "days_remaining": 0,
        "available": False,
    }


@router.post("/buy", summary="购买会员（暂未开放）")
async def buy_member(
    request: MemberBuyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=PAYMENT_FEATURE_MESSAGE)


@router.post("/exchange", summary="兑换会员（暂未开放）")
async def exchange_member(
    request: MemberExchangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=PAYMENT_FEATURE_MESSAGE)


@router.get("/privileges", summary="会员权益（暂未开放）")
async def get_member_privileges():
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=PAYMENT_FEATURE_MESSAGE)
