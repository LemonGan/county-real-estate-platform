# 县域房产平台后端API

基于FastAPI构建的高性能异步后端服务。

## 技术栈

- **FastAPI** - 现代、快速的Web框架
- **MySQL** - 关系型数据库
- **SQLAlchemy** - ORM框架
- **Alembic** - 数据库迁移工具
- **Redis** - 缓存和会话存储
- **JWT** - 用户认证

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 3. 启动数据库（使用Docker）

```bash
docker-compose up -d db redis
```

### 4. 运行数据库迁移

```bash
alembic upgrade head
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 使用Docker运行

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

## 项目结构

```
backend/
├── app/
│   ├── api/          # API路由
│   ├── core/         # 核心配置
│   ├── crud/         # 数据库操作
│   ├── models/       # 数据模型
│   ├── schemas/      # Pydantic模型
│   ├── utils/        # 工具函数
│   └── main.py       # 应用入口
├── tests/             # 测试文件
├── alembic/           # 数据库迁移
└── requirements.txt   # 依赖列表
```

## 开发指南

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式化

```bash
black app/
isort app/
```

### 创建数据库迁移

```bash
alembic revision --autogenerate -m "描述信息"
alembic upgrade head
```

## API端点

- `/api/v1/auth/login` - 用户登录
- `/api/v1/auth/register` - 用户注册
- `/api/v1/users/me` - 获取当前用户信息
- `/api/v1/properties` - 房源管理
- `/api/v1/appointments` - 预约管理
- `/api/v1/tools/mortgage-calculator` - 房贷计算器

## 许可证

MIT License
