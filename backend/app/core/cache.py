"""
Redis缓存服务
"""
import json
import hashlib
from typing import Optional, Any, List
import redis.asyncio as aioredis
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis客户端实例
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """获取Redis客户端（单例模式）"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # 测试连接
            await _redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            _redis_client = None
    return _redis_client


async def close_redis_client():
    """关闭Redis连接"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class CacheService:
    """缓存服务类"""
    
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None
    
    async def _get_client(self) -> Optional[aioredis.Redis]:
        """获取Redis客户端"""
        if self.client is None:
            self.client = await get_redis_client()
        return self.client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        client = await self._get_client()
        if not client:
            return None
        
        try:
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        client = await self._get_client()
        if not client:
            return False
        
        try:
            await client.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
            return True
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        client = await self._get_client()
        if not client:
            return False
        
        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存"""
        client = await self._get_client()
        if not client:
            return 0
        
        try:
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"按模式删除缓存失败 {pattern}: {str(e)}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        client = await self._get_client()
        if not client:
            return False
        
        try:
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"检查缓存存在失败 {key}: {str(e)}")
            return False
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        if not kwargs:
            return prefix
        
        # 对参数进行排序并生成hash
        sorted_params = sorted(kwargs.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"


# 缓存键前缀常量
class CacheKeys:
    """缓存键前缀定义"""
    @staticmethod
    def property_detail(property_id: int) -> str:
        return f"property:{property_id}:detail"
    
    @staticmethod
    def property_list() -> str:
        return "properties:list"
    
    @staticmethod
    def property_search() -> str:
        return "properties:search"
    
    @staticmethod
    def user_preference(user_id: int) -> str:
        return f"user:{user_id}:preferences"
    
    @staticmethod
    def user_info(user_id: int) -> str:
        return f"user:{user_id}:info"
    
    @staticmethod
    def video_recommendation(user_id: int) -> str:
        return f"video:rec:{user_id}"
    
    @staticmethod
    def video_detail(video_id: int) -> str:
        return f"video:{video_id}:detail"
    
    @staticmethod
    def video_list() -> str:
        return "videos:list"
    
    @staticmethod
    def statistics_dashboard() -> str:
        return "statistics:dashboard"
    
    @staticmethod
    def statistics_properties() -> str:
        return "statistics:properties"
    
    @staticmethod
    def statistics_users() -> str:
        return "statistics:users"
    
    @staticmethod
    def statistics_appointments() -> str:
        return "statistics:appointments"
    
    @staticmethod
    def statistics_favorites() -> str:
        return "statistics:favorites"
    
    @staticmethod
    def appointment_detail(appointment_id: int) -> str:
        return f"appointment:{appointment_id}:detail"


# 缓存TTL常量（秒）
class CacheTTL:
    """缓存过期时间定义"""
    PROPERTY_DETAIL = 30 * 60  # 30分钟
    PROPERTY_LIST = 10 * 60  # 10分钟
    PROPERTY_SEARCH = 10 * 60  # 10分钟
    USER_PREFERENCE = 60 * 60  # 1小时
    USER_INFO = 30 * 60  # 30分钟
    VIDEO_RECOMMENDATION = 60 * 60  # 1小时
    VIDEO_DETAIL = 30 * 60  # 30分钟
    VIDEO_LIST = 10 * 60  # 10分钟
    STATISTICS = 5 * 60  # 5分钟
    APPOINTMENT_DETAIL = 5 * 60  # 5分钟


# 全局缓存服务实例
cache_service = CacheService()
