"""
配置管理模块
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "县域房产平台"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "县域房产信息平台API"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="mysql+asyncmy://xqfc_user:password@localhost:3306/xqfc_db",
        description="数据库连接URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    
    # 安全配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 7,  # 7天
        description="访问令牌过期时间（分钟）"
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 14,  # 14天
        description="刷新令牌过期时间（分钟）"
    )
    
    # 调试模式
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost", "http://localhost:8080"],
        description="允许的CORS源"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 文件上传配置
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="最大文件大小（字节）"
    )
    UPLOAD_DIR: str = Field(
        default="./uploads",
        description="上传文件目录"
    )
    STATIC_DIR: str = Field(
        default="./static",
        description="静态文件目录"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="./logs/app.log", description="日志文件路径")
    
    # 微信小程序配置
    WECHAT_APPID: Optional[str] = Field(default=None, description="微信小程序AppID")
    WECHAT_SECRET: Optional[str] = Field(default=None, description="微信小程序Secret")
    WECHAT_LOGIN_URL: str = Field(
        default="https://api.weixin.qq.com/sns/jscode2session",
        description="微信登录API地址"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
