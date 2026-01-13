"""
数据库初始化脚本
"""
import asyncio
from app.core.database import init_db, engine, Base
from app.models import User, Property, Appointment  # 导入所有模型


async def main():
    """初始化数据库"""
    print("开始初始化数据库...")
    await init_db()
    print("数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
