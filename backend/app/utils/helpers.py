"""
辅助工具函数
"""
from typing import Any, Dict
from datetime import datetime
import json


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_price(price: float) -> str:
    """格式化价格显示"""
    if price >= 10000:
        return f"{price/10000:.2f}万"
    return f"{price:.0f}元"


def format_area(area: float) -> str:
    """格式化面积显示"""
    return f"{area:.2f}㎡"


def create_response(data: Any = None, message: str = "success", code: int = 0) -> Dict:
    """创建统一响应格式"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
