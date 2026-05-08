"""
会员管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


# 会员配置
MEMBER_CONFIG = {
    1: {"name": "月卡", "days": 30, "price": 9.9},
    2: {"name": "季卡", "days": 90, "price": 19.9},
    3: {"name": "年卡", "days": 365, "price": 59.9},
}

# 兑换码配置
MEMBER_CODES = {
    "VIP888": {"level": 3, "days": 365, "name": "年卡兑换码"},
    "VIP666": {"level": 2, "days": 90, "name": "季卡兑换码"},
    "VIP333": {"level": 1, "days": 30, "name": "月卡兑换码"},
    "TEST7": {"level": 1, "days": 7, "name": "试用7天"},
}


class MemberBuyRequest(BaseModel):
    level: int  # 1月卡 2季卡 3年卡


class MemberExchangeRequest(BaseModel):
    code: str


class MemberStatusResponse(BaseModel):
    is_member: bool
    member_level: int
    member_expire: Optional[str]
    days_remaining: int


def check_is_member(user: User) -> bool:
    """检查用户是否是有效会员"""
    if user.member_level == 0:
        return False
    if user.member_expire and user.member_expire > datetime.now():
        return True
    return False


@router.get("/status", response_model=MemberStatusResponse, summary="获取会员状态")
async def get_member_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的会员状态"""
    is_member = check_is_member(current_user)
    days_remaining = 0
    
    if is_member and current_user.member_expire:
        delta = current_user.member_expire - datetime.now()
        days_remaining = max(0, delta.days)
    
    return {
        "is_member": is_member,
        "member_level": current_user.member_level,
        "member_expire": current_user.member_expire.isoformat() if current_user.member_expire else None,
        "days_remaining": days_remaining
    }


@router.post("/buy", summary="购买会员")
async def buy_member(
    request: MemberBuyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """购买会员（简化版：直接开通）"""
    if request.level not in MEMBER_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会员等级"
        )
    
    config = MEMBER_CONFIG[request.level]
    
    # 计算新的到期时间
    if current_user.member_expire and current_user.member_expire > datetime.now():
        # 续期
        new_expire = current_user.member_expire + timedelta(days=config["days"])
    else:
        # 新开
        new_expire = datetime.now() + timedelta(days=config["days"])
    
    current_user.member_level = request.level
    current_user.member_expire = new_expire
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "success": True,
        "member_level": current_user.member_level,
        "member_expire": new_expire.isoformat(),
        "message": f"成功开通{config['name']}，到期时间：{new_expire.strftime('%Y-%m-%d')}"
    }


@router.post("/exchange", summary="兑换会员")
async def exchange_member(
    request: MemberExchangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """使用兑换码兑换会员"""
    code = request.code.upper()
    
    if code not in MEMBER_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的兑换码"
        )
    
    config = MEMBER_CODES[code]
    
    # 计算新的到期时间
    if current_user.member_expire and current_user.member_expire > datetime.now():
        new_expire = current_user.member_expire + timedelta(days=config["days"])
    else:
        new_expire = datetime.now() + timedelta(days=config["days"])
    
    current_user.member_level = config["level"]
    current_user.member_expire = new_expire
    current_user.member_code = code
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "success": True,
        "member_level": current_user.member_level,
        "member_expire": new_expire.isoformat(),
        "message": f"兑换成功！已开通{config['name']}，到期时间：{new_expire.strftime('%Y-%m-%d')}"
    }


@router.get("/privileges", summary="会员权益说明")
async def get_member_privileges():
    """获取会员权益说明"""
    return {
        "普通用户": {
            "电话咨询": "每天1次",
            "预约看房": "每天1次",
            "房贷计算": "基础版",
            "房源收藏": "最多5套"
        },
        "会员用户": {
            "电话咨询": "无限制",
            "预约看房": "无限制",
            "房贷计算": "高级版（税费+装修）",
            "房源收藏": "无限制",
            "专属客服": "优先服务"
        },
        "会员特权": {
            "1": {"name": "月卡", "days": 30, "price": 9.9},
            "2": {"name": "季卡", "days": 90, "price": 19.9},
            "3": {"name": "年卡", "days": 365, "price": 59.9}
        }
    }
