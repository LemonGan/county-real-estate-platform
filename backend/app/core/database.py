"""
数据库连接和会话管理
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator, Optional

from app.core.config import settings

# 创建基础模型类
Base = declarative_base()

# 延迟创建引擎（避免在Alembic迁移时创建）
engine: Optional[create_async_engine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None

# 如果不在Alembic迁移环境中，创建引擎
if not os.environ.get("ALEMBIC_MIGRATION"):
    # 创建异步数据库引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    # 创建异步会话工厂
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话依赖
    用于FastAPI的依赖注入
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database engine not initialized")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）"""
    if engine is None:
        raise RuntimeError("Database engine not initialized")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    if engine is not None:
        await engine.dispose()
