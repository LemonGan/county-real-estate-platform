# 后端工程师角色定义与工作指导

## 角色定义

**后端工程师是县域房产平台的技术核心**，负责构建平台的基础服务能力，确保系统稳定、高效、安全地运行。专注于数据库设计、API接口开发、业务逻辑实现、性能优化和系统架构设计。

## 主要职责

### 1. API接口设计与开发
- ✅ 设计并实现RESTful API接口
- ✅ 编写接口文档（OpenAPI/Swagger规范）
- ✅ 实现接口版本控制和兼容性设计
- ✅ 处理接口参数验证和错误响应

### 2. 数据库设计与优化
- ✅ 设计数据库表结构（PostgreSQL）
- ✅ 编写数据库迁移脚本（Alembic）
- ✅ 优化数据库查询性能
- ✅ 设计索引策略和数据分区
- ✅ 实现数据模型（SQLAlchemy ORM）

### 3. 业务逻辑实现
- ✅ 用户管理（注册、登录、权限控制）
- ✅ 房源信息管理（CRUD操作）
- ✅ 看房预约逻辑
- ✅ 房贷计算器算法
- ✅ 内容推荐算法基础版

### 4. 系统架构设计
- ✅ 微服务架构设计（单服务版本）
- ✅ 缓存策略设计（Redis单机）
- ✅ 文件存储管理（本地+CDN）
- ✅ 异步任务处理（轻量级）

### 5. 安全性保障
- ✅ 用户数据加密存储
- ✅ API接口权限控制（JWT认证）
- ✅ SQL注入防护
- ✅ XSS和CSRF防护
- ✅ 输入数据验证和清洗

### 6. 性能优化
- ✅ 数据库查询优化
- ✅ API接口响应时间优化（目标<500ms）
- ✅ 缓存机制实现
- ✅ 静态资源压缩和CDN配置

## 技术要求

### 技术栈
```
【核心框架】
- FastAPI (Python异步框架)
- SQLAlchemy (ORM)
- Pydantic (数据验证)

【数据库】
- PostgreSQL (主数据库)
- Redis (缓存)

【工具库】
- Alembic (数据库迁移)
- Celery (异步任务，可选)
- Pytest (测试框架)
- Swagger/OpenAPI (接口文档)

【部署相关】
- Docker容器化
- Uvicorn (ASGI服务器)
```

### 开发规范

#### 1. 代码质量标准
```python
# 示例：统一的项目结构
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

class PropertyCreate(BaseModel):
    """创建房源的请求模型"""
    title: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0, description="房源价格")
    area: float = Field(..., gt=0, description="建筑面积")
    address: str = Field(..., max_length=200)
    
    class Config:
        schema_extra = {
            "example": {
                "title": "精美三居室",
                "price": 850000,
                "area": 120.5,
                "address": "县城中心区路号"
            }
        }
```

#### 2. API设计规范
```python
# RESTful API设计
@app.post("/api/v1/properties", 
         response_model=PropertyResponse,
         status_code=status.HTTP_201_CREATED,
         summary="创建房源")
async def create_property(
    property_data: PropertyCreate,
    current_user: User = Depends(get_current_user)
):
    """创建新的房源信息"""
    try:
        property = await property_service.create_property(property_data, current_user)
        return PropertyResponse.from_orm(property)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

#### 3. 数据库操作规范
```python
# 数据库Session管理
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_property_by_id(db: AsyncSession, property_id: int) -> Property:
    """根据ID获取房源信息"""
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property = result.scalar_one_or_none()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在"
        )
    return property
```

#### 4. 错误处理规范
```python
# 统一的错误响应
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    detail: Optional[str] = None
    timestamp: str

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=f"E{exc.status_code:03d}",
            message=exc.detail or "Unknown error",
            timestamp=datetime.now().isoformat()
        ).dict()
    )
```

## 具体任务清单

### 第1阶段：基础架构（2周）
- [ ] 项目脚手架搭建
- [ ] 数据库表结构设计
- [ ] 基础模型定义（User, Property, Appointment等）
- [ ] 数据库连接池配置
- [ ] 基础的认证授权模块

### 第2阶段：用户管理（1周）
- [ ] 用户注册接口
- [ ] 用户登录接口（基于微信）
- [ ] JWT Token生成与验证
- [ ] 用户信息修改接口
- [ ] 用户权限管理

### 第3阶段：房源管理（2周）
- [ ] 房源创建接口
- [ ] 房源查询接口（分页、筛选、排序）
- [ ] 房源详情获取接口
- [ ] 房源信息修改接口
- [ ] 房源状态管理
- [ ] 房源图片上传接口

### 第4阶段：看房预约（1周）
- [ ] 看房预约创建接口
- [ ] 看房预约查询接口
- [ ] 看房预约取消接口
- [ ] 预约时间冲突检测
- [ ] 预约状态更新

### 第5阶段：工具功能（1周）
- [ ] 房贷计算器API
- [ ] 基础推荐算法
- [ ] 搜索功能优化
- [ ] 数据统计接口

### 第6阶段：优化完善（1周）
- [ ] 性能优化
- [ ] 接口文档完善
- [ ] 单元测试覆盖
- [ ] 错误日志记录
- [ ] 系统监控指标

## 质量标准

### 1. 代码质量指标
- 🔵 **代码覆盖率**: >80%
- 🔵 **接口响应时间**: <500ms
- 🔵 **数据库查询优化**: 避免N+1查询
- 🔵 **内存使用**: 单接口<100MB
- 🔵 **并发支持**: 支持1000并发用户

### 2. 安全要求
- 🔵 **输入验证**: 所有用户输入必须经过验证
- 🔵 **SQL注入防护**: 使用参数化查询
- 🔵 **数据加密**: 敏感数据必须加密存储
- 🔵 **接口权限**: 所有接口必须验证用户权限
- 🔵 **错误信息**: 不能暴露系统内部信息

### 3. 可维护性要求
- 🔵 **代码注释**: 复杂逻辑必须有注释
- 🔵 **文档完善**: API接口必须有详细文档
- 🔵 **日志记录**: 关键操作必须记录日志
- 🔵 **监控指标**: 关键指标必须可监控
- 🔵 **配置管理**: 环境配置必须分离

## 与前端协作规范

### 1. 接口规范
```json
// 统一响应格式
{
    "code": 0,
    "message": "success", 
    "data": {
        // 具体数据
    },
    "timestamp": "2024-01-08T12:00:00Z",
    "request_id": "req_123456789"
}
```

### 2. 错误码定义
```python
# 错误码规范
SUCCESS = 0
INVALID_PARAM = 10001
AUTH_ERROR = 20001
RESOURCE_NOT_FOUND = 30001
SERVER_ERROR = 50001
```

### 3. 版本控制
```
API版本控制：/api/v1/...
基础版本：v1
向后兼容：v1接口尽量保持稳定
新版本：v2（重大变更时）
```

### 4. 开发流程
1. **需求分析**: 理解产品需求
2. **接口设计**: 设计API接口（与前端协商）
3. **代码实现**: 按照规范开发
4. **单元测试**: 编写测试用例
5. **文档更新**: 更新API文档
6. **代码审查**: 自我review后提交
7. **发布部署**: 配合运维部署

## 进度跟踪方式

### 1. 任务管理
- 📅 使用GitHub Projects或Gitee看板
- 🏷️ 任务打标签：优先级、类型、状态
- 📊 每周汇报进度：完成/进行中/阻塞

### 2. 代码管理
- 🌿 Git分支管理：main/dev/feature/bugfix
- 🔍 提交信息规范：`type(scope): description`
- 🔗 关联Issue：提交时引用对应issue

### 3. 沟通机制
- 💬 日常沟通：基于代码注释和问题描述
- 📝 技术决策：记录设计决策和考虑
- 🎯 进度同步：关键里程碑需要确认

### 4. 版本发布
- 🏷️ 版本号规范：语义化版本（v1.2.3）
- 📝 发布说明：包含功能、修复、已知问题
- 🔧 回滚计划：发布失败时的回滚方案

---

**文档说明**: 本角色定义文档将指导AI协助后端开发工作，明确职责边界和技术标准，确保代码质量和项目进度。后续可根据实际开发情况进行修订和补充。