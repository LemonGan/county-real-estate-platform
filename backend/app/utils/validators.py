"""
自定义验证器
"""
import re
from typing import Any


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_password(password: str) -> bool:
    """验证密码强度"""
    # 至少6位，包含字母和数字
    if len(password) < 6:
        return False
    if not re.search(r'[a-zA-Z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True
