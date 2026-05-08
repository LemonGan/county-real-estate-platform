"""
请求频率限制工具（内存版，单进程适用）
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status

# 存储: { "ip:endpoint": [timestamp, ...] }
_store = defaultdict(list)

# 默认配置
DEFAULT_WINDOW = 60      # 时间窗口（秒）
DEFAULT_MAX_REQUESTS = 30  # 窗口内最大请求数
AUTH_MAX_REQUESTS = 10    # 登录/注册接口限制


def _cleanup():
    """清理过期的记录"""
    now = time.time()
    for key in list(_store.keys()):
        _store[key] = [t for t in _store[key] if now - t < DEFAULT_WINDOW * 2]
        if not _store[key]:
            del _store[key]


class RateLimiter:
    """频率限制器"""

    def __init__(self, max_requests: int = DEFAULT_MAX_REQUESTS, window: int = DEFAULT_WINDOW):
        self.max_requests = max_requests
        self.window = window

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        now = time.time()

        # 清理旧记录
        _store[key] = [t for t in _store[key] if now - t < self.window]

        if len(_store[key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )

        _store[key].append(now)
        # 定期清理全局数据
        if len(_store) > 1000:
            _cleanup()


# 预定义限制器
default_limiter = RateLimiter()
auth_limiter = RateLimiter(max_requests=AUTH_MAX_REQUESTS, window=60)
