"""
Alembic环境配置
"""
import os
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 设置环境变量，告诉database.py不要创建引擎
os.environ["ALEMBIC_MIGRATION"] = "1"

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# 导入应用配置
from app.core.config import settings

# 导入Base和所有模型
# 注意：由于设置了环境变量，database.py不会创建引擎
from app.core.database import Base
from app.models import (
    User, UserPreference, UserBehavior,
    Property, PropertyImage, PropertyFavorite,
    Appointment, AgentAvailability,
    ShortVideo, VideoRecommendation
)

# Alembic配置对象
config = context.config

# 设置数据库URL（Alembic需要同步驱动）
# 将asyncmy替换为pymysql用于Alembic迁移
db_url = settings.DATABASE_URL.replace("+asyncmy", "+pymysql")
config.set_main_option("sqlalchemy.url", db_url)

# 如果定义了日志配置，则使用它
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移（使用同步引擎）"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
