"""
微信相关工具函数
"""
import httpx
import logging
from typing import Optional, Dict
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


async def get_wechat_openid(code: str) -> Dict[str, str]:
    """
    通过微信code获取openid和session_key
    
    Args:
        code: 微信小程序登录凭证code
    
    Returns:
        Dict包含openid和session_key
    """
    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信小程序配置未设置"
        )
    
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.WECHAT_LOGIN_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 检查是否有错误
            if "errcode" in data:
                error_msg = data.get("errmsg", "未知错误")
                logger.error(f"微信登录失败: {error_msg} (errcode: {data.get('errcode')})")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"微信登录失败: {error_msg}"
                )
            
            # 返回openid和session_key
            if "openid" not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="微信登录响应中缺少openid"
                )
            
            return {
                "openid": data["openid"],
                "session_key": data.get("session_key", ""),
                "unionid": data.get("unionid")  # 可选，需要开放平台
            }
    except httpx.HTTPError as e:
        logger.error(f"调用微信API失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信服务暂时不可用，请稍后重试"
        )
    except Exception as e:
        logger.error(f"微信登录处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信登录处理失败"
        )
