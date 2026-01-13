"""
认证相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class WeChatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str = Field(..., description="微信小程序登录凭证code")
    nickname: Optional[str] = Field(None, max_length=50, description="用户昵称（可选）")
    avatar: Optional[str] = Field(None, max_length=500, description="用户头像URL（可选）")


class Token(BaseModel):
    """令牌响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user_id: Optional[int] = Field(None, description="用户ID")
    is_new_user: Optional[bool] = Field(None, description="是否为新用户")