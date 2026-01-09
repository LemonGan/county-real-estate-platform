# GitHub项目创建与配置指南

## 项目仓库创建步骤

### 1. GitHub项目初始化

#### 1.1 创建新仓库
在GitHub上创建项目仓库：

```bash
# 建议的仓库设置
Repository name: county-real-estate-platform
Description: 县域房产信息平台 - 基于FastAPI + WeChat MiniProgram
Visibility: Public (开源项目) or Private (初期建议Private)
Initialize this repository with: ☐ 不勾选任何选项
```

#### 1.2 本地项目初始化
```bash
# 在本地创建项目目录
mkdir county-real-estate-platform
cd county-real-estate-platform

# 初始化Git仓库
git init

# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/county-real-estate-platform.git

# 添加所有文件
git add .
git commit -m "Initial project setup 🎉"

# 推送到远程仓库
git push -u origin main
```

### 1.3 仓库设置与配置

#### 仓库基本信息设置
```markdown
Repository Name: county-real-estate-platform
Description: 县域房产信息平台 - FastAPI后端 + 微信小程序前端 + AI协作开发
Topics: fastapi, wechat-miniprogram, real-estate, china-county, ai-collaboration
Default Branch: main
```

#### 分支保护规则
```markdown
# 分支保护规则设置
Branch: main
Requirements:
✅ Require a pull request before merging
✅ Require status checks to pass before merging
✅ Require branches to be up to date before merging
✅ Include administrators
```

## 2. 项目目录结构搭建

### 2.1 推荐的目录结构
```
county-real-estate-platform/
├── backend/                    # FastAPI后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI应用入口
│   │   ├── config.py          # 配置文件
│   │   ├── api/               # API路由
│   │   ├── core/              # 核心功能
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # 序列化/验证模型
│   │   ├── crud/              # 数据库操作
│   │   ├── db/                # 数据库连接
│   │   ├── tests/             # 测试文件
│   │   └── utils/             # 工具函数
│   ├── alembic/               # 数据库迁移
│   ├── docker/                # Docker相关文件
│   ├── scripts/               # 辅助脚本
│   ├── tests/                 # 后端测试
│   ├── requirements.txt       # 依赖列表
│   ├── Dockerfile             # 容器化配置
│   └── pyproject.toml         # Poetry项目管理
├── miniprogram/              # 微信小程序前端
│   ├── app.js                # 小程序全局应用
│   ├── app.json              # 小程序配置
│   ├── app.wxss              # 小程序全局样式
│   ├── pages/                # 页面目录
│   │   ├── index/            # 首页页面
│   │   ├── property/         # 房源相关页面
│   │   ├── user/             # 用户相关页面
│   │   ├── tools/            # 工具页面
│   │   └── auth/             # 认证相关页面
│   ├── components/           # 自定义组件
│   ├── utils/                # 工具函数
│   ├── assets/               # 静态资源
│   ├── libs/                 # 第三方库
│   └── images/               # 图片资源
├── devops/                   # DevOps配置
│   ├── docker-compose.yml    # 容器编排
│   ├── nginx/                # Nginx配置
│   ├── prometheus/           # 监控配置
│   ├── scripts/              # 运维脚本
│   └── docs/                 # 运维文档
├── docs/                     # 项目文档
│   ├── api/                  # API文档
│   ├── design/               # 设计文档
│   └── guides/               # 开发指南
├── .github/                  # GitHub Actions配置
│   ├── workflows/            # CI/CD工作流
│   ├── ISSUE_TEMPLATE/       # Issue模板
│   └── pull_request_template.md
├── .gitignore               # Git忽略文件
├── README.md                # 项目说明文档
├── CONTRIBUTING.md          # 贡献指南
├── LICENSE                  # 开源许可证
└── .env.example            # 环境变量模板
```

### 2.2 核心配置文件

#### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.ropeproject/
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.production

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Database
*.db
*.sqlite3

# Coverage
htmlcov/
.coverage
.coverage.*

# Presentation files
storage/
media/*
!media/.gitkeep
static/*
!static/.gitkeep

# macOS
.DS_Store
.AppleDouble
.LSOverride

# Windows
ehthumbs.db
Thumbs.db
desktop.ini

# Docker
.dockerignore

# Backup files
*.bak
*.backup
```

#### pyproject.toml (后端项目管理)
```toml
[tool.poetry]
name = "county-real-estate-backend"
version = "0.1.0"
description = "县域房产平台后端服务"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [{include = "app"}]

[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.23"
asyncpg = "^0.29.0"
alembic = "^1.12.1"
pydantic = {extras = ["email"], version = "^2.5.0"}
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
redis = "^5.0.1"
aiocache = "^0.12.2"
httpx = "^0.25.2"
aiofiles = "^23.2.1"
python-multipart = "^0.0.6"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
black = "^23.11.0"
isort = "^5.12.0"
flake8 = "^6.1.0"
mypy = "^1.7.1"

[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | src
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

## 3. Git工作流建立

### 3.1 分支策略（Git Flow简化版）
```
main                    # 生产分支 - 稳定代码
├── dev                 # 开发分支 - 最新功能
├── feature/*           # 功能分支 - 开发新功能
├── hotfix/*            # 热修复分支 - 紧急修复
└── release/*           # 发布分支 - 版本准备
```

#### 分支建立和使用
```bash
# 创建开发分支
git checkout -b dev
git push -u origin dev

# 创建功能分支示例
git checkout dev
git checkout -b feature/user-authentication
git push -u origin feature/user-authentication

# 工作完成后合并回dev分支
git checkout dev
git merge feature/user-authentication
git push origin dev
```

### 3.2 Commit规范（Conventional Commits）
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 提交类型
```
feat:     新功能 (feature)
fix:      Bug修复 (bug fix)
docs:     文档更新 (documentation)
style:    格式变更 (formatting, missing semi colons, etc)
refactor: 重构 (neither fixes a bug nor adds a feature)
perf:     性能优化 (performance improvements)
test:     测试相关 (adding missing tests, refactoring tests)
build:    构建相关 (affecting the build system or external dependencies)
ci:       持续集成相关 (changes to CI scripts, workflows)
chore:    杂项 (updating dependencies, configurations)
revert:   回退操作 (reverting a previous commit)
```

#### Commit示例
```bash
git commit -m "feat(auth): add user registration endpoint with phone verification

- Implemented /api/v1/auth/register endpoint
- Added phone format validation
- Integrated with SMS service placeholder
- Added corresponding unit tests

Related issue: #12"
```

## 4. 仓库元数据配置

### 4.1 README模板
```markdown
# 县域房产信息平台 (county-real-estate-platform)

<div align="center">
  
  !License, [MIT](./LICENSE) * [中文](./README_CN.md)]
  
</div>

## 🏠 项目介绍

县域房产信息平台是一个专注于三四线城市且县城地区的房产信息分享平台，通过短视频内容与信息服务 + 看房预约的模式，为返乡置业用户和本地居民提供可信、便捷的房源信息。

### 🌟 主要特色
- **专注县域市场**：填补大平台覆盖空白
- **短视频营销**：紧跟抖音流量趋势
- **轻量级架构**：适合个人开发者独立运维
- **AI协作开发**：最大化提升开发效率

### 🎯 目标用户
- 返乡置业人群（核心用户）
- 本地改善型购房者
- 县域房产投资者

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能异步Python Web框架
- **PostgreSQL** - 主要数据存储
- **Redis** - 缓存和会话存储
- **Alembic** - 数据迁移工具
- **JWT** - 用户认证

### 前端
- 微信小程序原生开发
- WXML/WXSS
- ES6+ JavaScript
- Vant Weapp UI组件库

### DevOps & 工具
- **Docker** - 容器化部署
- **Nginx** - 反向代理
- **GitHub Actions** - CI/CD
- **Prometheus** - 监控

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+ (用于小程序开发)
- Docker & Docker Compose
- Git

### 后端启动
```bash
# 1. 环境准备
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 2. 安装依赖
pip install poetry
poetry install

# 3. 环境变量配置
cp .env.example .env
# 编辑 .env 文件

# 4. 数据库准备
docker-compose up -d postgres redis
poetry run alembic upgrade head

# 5. 启动服务
poetry run uvicorn app.main:app --reload
```

### 前端开发
```bash
# 1. 打开微信开发者工具
# 2. 导入 miniprogram 目录
# 3. 修改配置文件
# 4. 开始开发和调试
```

## 📋 功能特性

### 已实现功能 ✅
- 用户注册/登录（手机号+验证码）
- 房源信息管理（CRUD）
- 看房预约系统
- 房贷计算器工具
- 房源搜索和筛选
- 图片和VR展示
- 短视频内容集成

### 计划中功能 📋
- 消息通知中心
- 房产经纪人认证系统
- 房产估价工具
- 移动端适配优化

## 🏗️ 项目结构

```
county-real-estate-platform/
├── backend/                    # FastAPI后端服务
│   ├── app/                    # 应用代码
│   ├── requirements.txt        # Python依赖
│   ├── Dockerfile              # 容器化配置
│   └── pyproject.toml         # Poetry配置
├── miniprogram/               # 微信小程序前端
│   ├── pages/                 # 页面文件
│   ├── components/            # 自定义组件
│   └── utils/                 # 工具函数
├── devops/                    # 运维配置
│   ├── docker-compose.yml     # 容器编排
│   └── nginx/                 # Nginx配置
└── docs/                      # 项目文档
```

## 🧪 如何运行测试

```bash
# 后端测试
cd backend
poetry run pytest tests/ -v --cov=app

# 前端小程序测试
# 使用微信开发者工具测试功能
# 或使用 wechat-miniprogram-automator
```

## 📊 性能基准

- 接口平均响应时间: < 500ms
- P95响应时间: < 1000ms
- 并发用户支持: > 1000用户
- 数据查询优化: 利用索引和缓存

## 🔧 开发指南

### 贡献指南
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范
- 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 
- 后端遵循 PEP8 规范
- 前端遵循微信小程序开发规范
- 代码必须通过测试和审查

## 📈 项目进度

查看 [Projects](https://github.com/YOUR_USERNAME/county-real-estate-platform/projects) 页面了解当前开发进度。

## 🔄 更新日志

查看 [CHANGELOG.md](./CHANGELOG.md) 了解版本更新内容。

## 🤝 贡献指南

请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解如何为本项目做出贡献。

## 📄 许可证

本项目采用 [MIT 许可证](./LICENSE) - 查看文件了解详情。

## ✨ 致谢

- 感谢 FastAPI 框架带来的开发效率提升
- 感谢微信开放平台提供的小程序技术支持
- 感谢所有 AI 工具在开发过程中的协助
- 感谢县域房产从业者提供的业务指导

## 📞 联系我们

- 📧 邮箱: [your.email@example.com](mailto:your.email@example.com)
- 🐛 Bug报告: [Issues](https://github.com/YOUR_USERNAME/county-real-estate-platform/issues)
- 💡 功能建议: [Discussions](https://github.com/YOUR_USERNAME/county-real-estate-platform/discussions)

---

<div align="center">
  <b>⭐ 如果这个项目对你有帮助，请给个 Star 支持一下!</b>
</div>
```

### 4.2 LICENSE文件
```markdown
MIT License

Copyright (c) 2024 县域房产信息平台

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 4.3 CONTRIBUTING.md
```markdown
# 贡献指南

欢迎各位开发者为县域房产信息平台项目做出贡献！

## 🤝 如何贡献

### 报告问题
- 使用 [Issue 模板](https://github.com/YOUR_USERNAME/county-real-estate-platform/issues/new/choose)
- 详细描述问题复现步骤
- 提供环境和版本信息
- 附加截图或日志信息

### 提交代码
1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交你的修改：`git commit -m 'feat: Add your feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 代码风格要求
- 遵循项目已有的代码风格
- 后端代码遵循 PEP8 规范
- 前端遵循微信小程序开发规范
- 编写适当的注释和文档
- 添加必要的测试用例

## 📝 Commit 规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式变更
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `build`: 构建相关
- `ci`: CI/CD相关
- `chore`: 杂项任务
- `revert`: 回退操作

### 示例
```
feat(auth): add phone verification during signup

- Implement SMS sending functionality
- Add verification code validation
- Update user registration flow

Closes #23
```

## 🧪 测试要求

- 所有新功能必须包含测试用例
- 保持测试覆盖率不低于 80%
- 运行完整的测试套件后再提交

## 📋 提交流程检查清单

- [ ] 代码通过了所有测试
- [ ] 遵循了项目的编码规范
- [ ] 添加了适当的注释和文档
- [ ] Commit 信息符合规范
- [ ] 更新了相关的 CHANGELOG

## 📞 联系信息

有任何问题或建议，欢迎通过以下方式联系：

- 创建 [Issue](https://github.com/YOUR_USERNAME/county-real-estate-platform/issues)
- 发起 [Discussion](https://github.com/YOUR_USERNAME/county-real-estate-platform/discussions)
- 发送邮件到：your.email@example.com

## 🙏 感谢

感谢你的贡献，让我们一起让县域房产信息平台变得更好！
```

## 5. CI/CD初始配置

### 5.1 GitHub Actions工作流（基础版）
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

env:
  PYTHON_VERSION: 3.9
  NODE_VERSION: 16

jobs:
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: latest
        virtualenvs-create: true
        virtualenvs-in-project: true
    
    - name: Load cached venv
      id: cached-poetry-dependencies
      uses: actions/cache@v3
      with:
        path: .venv
        key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}
    
    - name: Install dependencies
      if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
      run: poetry install --no-interaction --no-ansi
      working-directory: backend
    
    - name: Run backend linters
      run: |
        poetry run flake8 app/
        poetry run black --check app/
        poetry run isort --check-only app/
      working-directory: backend
    
    - name: Run backend tests
      run: |
        poetry run pytest tests/ -v --cov=app --cov-report=xml
      working-directory: backend
      env:
        DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        TESTING: true
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: backend/coverage.xml
        flags: backend
        name: backend-coverage

  frontend-checks:
    name: Frontend Checks
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'npm'
        cache-dependency-path: miniprogram/package-lock.json
    
    - name: Install dependencies
      run: |
        cd miniprogram
        npm install
        
    - name: Run frontend linting
      run: |
        cd miniprogram
        npm run lint
      
    - name: Build frontend (验证构建)
      run: |
        cd miniprogram
        npm run build
```

### 5.2 Issue和PR模板

#### Issue模板
```markdown
<!-- 使用以下标签：bug / enhancement / discussion / question -->

## 问题描述
简短清晰地描述问题或功能建议

## 重现步骤（适用于Bug）
1. 第一步...
2. 第二步...
3. 第三步...

## 期望行为
描述你期望发生的行为

## 实际行为
描述实际发生的行为

## 环境信息
- 操作系统: [e.g. iOS 16.0, Android 12.0]
- 微信版本: [e.g. 8.0.31]
- 小程序版本: [e.g. 1.0.0]
- 后端版本: [e.g. 0.1.0]

## 截图
如果适用，请添加截图以帮助解释问题

## 附加信息
添加任何其他上下文信息