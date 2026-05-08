"""
经纪人认证API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


class AgentApplyRequest(BaseModel):
    real_name: str
    id_card: str
    agent_license: str
    company: str
    phone: str


@router.post("/apply", summary="申请成为经纪人")
async def apply_as_agent(
    request: AgentApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.is_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经是经纪人了"
        )
    
    current_user.real_name = request.real_name
    current_user.id_card = request.id_card
    current_user.agent_license = request.agent_license
    current_user.phone = request.phone
    current_user.is_agent = True
    current_user.is_verified = True
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "user_id": current_user.id,
        "status": "approved",
        "message": "申请成功，您已成为经纪人"
    }


@router.get("/status", summary="获取经纪人状态")
async def get_agent_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return {
        "is_agent": current_user.is_agent,
        "is_verified": current_user.is_verified,
        "real_name": current_user.real_name,
        "agent_license": current_user.agent_license
    }
