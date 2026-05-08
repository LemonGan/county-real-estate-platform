"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.rate_limit import auth_limiter
from app.schemas.auth import Token, LoginRequest, WeChatLoginRequest
from app.crud.user import (
    get_user_by_phone, create_user, get_user_by_openid, get_user_by_unionid,
    create_wechat_user, update_wechat_user_info
)
from app.schemas.user import UserCreate
from app.utils.wechat import get_wechat_openid

router = APIRouter()


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户登录接口"""
    await auth_limiter(request)
    # 查找用户
    user = await get_user_by_phone(db, phone=login_data.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # 验证密码
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户未激活"
        )
    
    # 创建令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=Token, summary="用户注册")
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户注册接口"""
    await auth_limiter(request)
    # 检查手机号是否已存在
    existing_user = await get_user_by_phone(db, phone=user_data.phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已被注册"
        )
    
    # 创建用户
    user = await create_user(db, user_data)
    
    # 创建令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/wechat/login", response_model=Token, summary="微信登录")
async def wechat_login(
    wechat_data: WeChatLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """微信小程序登录接口"""
    await auth_limiter(request)
    # 通过code获取openid和session_key
    wechat_info = await get_wechat_openid(wechat_data.code)
    openid = wechat_info["openid"]
    session_key = wechat_info["session_key"]
    unionid = wechat_info.get("unionid")
    
    # 查找用户（优先通过unionid，其次openid）
    user = None
    if unionid:
        user = await get_user_by_unionid(db, unionid)
    
    if not user:
        user = await get_user_by_openid(db, openid)
    
    is_new_user = False
    
    # 如果用户不存在，创建新用户
    if not user:
        user = await create_wechat_user(
            db,
            openid=openid,
            session_key=session_key,
            unionid=unionid,
            nickname=wechat_data.nickname,
            avatar=wechat_data.avatar
        )
        is_new_user = True
    else:
        # 更新session_key和用户信息
        await update_wechat_user_info(
            db,
            user_id=user.id,
            session_key=session_key,
            nickname=wechat_data.nickname if wechat_data.nickname else None,
            avatar=wechat_data.avatar if wechat_data.avatar else None
        )
        # 如果用户有unionid但数据库中没有，更新unionid
        if unionid and not user.unionid:
            user.unionid = unionid
            await db.commit()
            await db.refresh(user)
    
    # 更新最后登录时间
    from datetime import datetime
    user.last_login_at = datetime.now()
    await db.commit()
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户未激活"
        )
    
    # 创建令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_new_user": is_new_user
    }
