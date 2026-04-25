"""
API v1版本路由
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, properties, appointments, tools, favorites, property_images, user_preferences, statistics, user_behaviors, short_videos, recommendations, news, agents, map, property_reviews, messages, upload, agent_auth, member

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(properties.router, prefix="/properties", tags=["房源"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["预约"])
api_router.include_router(tools.router, prefix="/tools", tags=["工具"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["收藏"])
api_router.include_router(property_images.router, prefix="", tags=["图片"])
api_router.include_router(user_preferences.router, prefix="/users", tags=["用户偏好"])
api_router.include_router(user_behaviors.router, prefix="/users", tags=["用户行为"])
api_router.include_router(short_videos.router, prefix="/short-videos", tags=["短视频"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["推荐算法"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["数据统计"])
api_router.include_router(news.router, prefix="/news", tags=["房产资讯"])
api_router.include_router(agents.router, prefix="/agents", tags=["经纪人"])
api_router.include_router(map.router, prefix="/map", tags=["地图"])
api_router.include_router(property_reviews.router, prefix="/properties", tags=["房源评价"])
api_router.include_router(messages.router, prefix="/messages", tags=["消息通知"])
api_router.include_router(upload.router, tags=["上传"])
api_router.include_router(agent_auth.router, prefix="/agent-auth", tags=["经纪人认证"])
api_router.include_router(member.router, prefix="/member", tags=["会员管理"])
