# 项目结构初始化脚本
import os
import json
from pathlib import Path

def create_project_structure():
    """创建完整的项目目录结构"""
    
    # 定义项目结构
    structure = {
        "backend": {
            "app": {
                "__init__.py": "",
                "main.py": "# FastAPI应用入口文件\nfrom fastapi import FastAPI\n\napp = FastAPI(title=\"县域房产平台API\", version=\"0.1.0\")\n\n@app.get(\"/health\")\nasync def health_check():\n    return {\"status\": \"healthy\", \"service\": \"county-real-estate-api\"}",
                "config.py": "# 配置管理\nfrom pydantic_settings import BaseSettings\nfrom typing import Optional\n\nclass Settings(BaseSettings):\n    database_url: str\n    redis_url: str\n    secret_key: str = \"your-secret-key-here\"\n    debug: bool = False\n    \n    class Config:\n        env_file = \".env\"\n\nsettings = Settings()",
                "api": {
                    "__init__.py": "",
                    "deps.py": "# 依赖注入",
                    "v1": {
                        "__init__.py": "",
                        "auth.py": "# 认证相关API",
                        "users.py": "# 用户管理API",
                        "properties.py": "# 房源管理API",
                        "appointments.py": "# 预约管理API",
                        "tools.py": "# 工具类API（房贷计算器）"
                    }
                },
                "core": {
                    "__init__.py": "",
                    "security.py": "# 安全相关工具",
                    "database.py": "# 数据库连接和会话管理"
                },
                "models": {
                    "__init__.py": "",
                    "user.py": "# 用户数据模型",
                    "property.py": "# 房源数据模型",
                    "appointment.py": "# 预约数据模型"
                },
                "schemas": {
                    "__init__.py": "",
                    "user.py": "# 用户数据验证模型",
                    "property.py": "# 房源数据验证模型",
                    "appointment.py": "# 预约数据验证模型"
                },
                "crud": {
                    "__init__.py": "",
                    "user.py": "# 用户数据库操作",
                    "property.py": "# 房源数据库操作",
                    "appointment.py": "# 预约数据库操作"
                },
                "utils": {
                    "__init__.py": "",
                    "validators.py": "# 自定义验证器",
                    "helpers.py": "# 辅助工具函数"
                }
            },
            "tests": {
                "__init__.py": "",
                "conftest.py": "# pytest配置",
                "test_auth.py": "# 认证测试",
                "test_users.py": "# 用户管理测试", 
                "test_properties.py": "# 房源管理测试",
                "test_appointments.py": "# 预约管理测试"
            },
            "alembic": {
                "alembic.ini": "# 数据迁移配置文件",
                "versions": {
                    ".gitkeep": ""
                }
            },
            "docker": {
                "Dockerfile": "FROM python:3.9-slim\n\nWORKDIR /app\n\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\n\nCOPY . .\n\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]",
                "docker-compose.dev.yml": "version: '3.8'\nservices:\n  postgres:\n    image: postgres:14\n    environment:\n      POSTGRES_DB: xqfc_dev\n      POSTGRES_USER: xqfc_user\n      POSTGRES_PASSWORD: dev_password\n    ports:\n      - \"5432:5432\"\n      \n  redis:\n    image: redis:7-alpine\n    ports:\n      - \"6379:6379\"\"
            },
            "scripts": {
                "create_superuser.py": "# 创建超级用户脚本",
                "init_db.py": "# 数据库初始化脚本",
                "backup_db.py": "# 数据库备份脚本"
            },
            "requirements.txt": """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
pydantic[email]==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
redis==5.0.1
aiocache==0.12.2
httpx==0.25.2
aiofiles==23.2.1
cryptography==41.0.7
pillow==10.1.0",
            "pyproject.toml": """[tool.poetry]\nname = \"county-real-estate-backend\"\nversion = \"0.1.0\"\ndescription = \"县域房产平台后端服务\"\nauthors = [\"Your Name <youremail@example.com>\"]\nreadme = \"README.md\"\npackages = [{include = \"app\"}]\n\n[tool.poetry.dependencies]\npython = \"^3.9\"\nfastapi = \"^0.104.1\"\nuvicorn = {extras = [\"standard\"], version = \"^0.24.0\"}\nsqlalchemy = \"^2.0.23\"\nasyncpg = \"^0.29.0\"\nalembic = \"^1.12.1\"\npython-jose = {extras = [\"cryptography\"], version = \"^3.3.0\"}\npasslib = {extras = [\"bcrypt\"], version = \"^1.7.4\"}\nredis = \"^5.0.1\"\naiocache = \"^0.12.2\"\npydantic = {\"^2.5.0\"}\n\n[tool.poetry.group.dev.dependencies]\npytest = \"^7.4.3\"\npytest-asyncio = \"^0.21.1\"\npytest-cov = \"^4.1.0\"\nblack = \"^23.11.0\"\nisort = \"^5.12.0\"\nflake8 = \"^6.1.0\"\nmypy = \"^1.7.1\"\n\n[build-system]\nrequires = [\"poetry-core\"]\nbuild-backend = \"poetry.core.masonry.api\"""
        },
        "miniprogram": {
            "app.js": "// 小程序全局应用\nApp({\n  onLaunch() {\n    console.log('县域房产平台小程序启动');\n    \n    // 初始化云开发环境（如需要）\n    // wx.cloud.init({\n    //   env: 'your-cloud-env-id',\n    // });\n    \n    // 检查用户登录状态\n    this.checkLoginStatus();\n  },\n  \n  globalData: {\n    userInfo: null,\n    token: null,\n    apiBaseUrl: 'https://api.xqfc.com/api/v1'  // 替换为你的API地址\n  },\n  \n  checkLoginStatus() {\n    // 检查本地存储的登录信息\n    const token = wx.getStorageSync('token');\n    const userInfo = wx.getStorageSync('userInfo');\n    \n    if (token \u0026\u0026 userInfo) {\n      this.globalData.token = token;\n      this.globalData.userInfo = userInfo;\n    }\n  }\n});",
            "app.json": '{\n  "pages": [\n    "pages/index/index",\n    "pages/property/list/index",\n    "pages/property/detail/index",\n    "pages/user/profile/index",\n    "pages/auth/login/index",\n    "pages/auth/register/index",\n    "pages/tools/mortgage-calc/index",\n    "pages/appointment/create/index",\n    "pages/appointment/list/index"\n  ],\n  "tabBar": {\n    "color": "#666",\n    "selectedColor": "#FF6B35",\n    "backgroundColor": "#fff",\n    "borderStyle": "black",\n    "list": [\n      {\n        "pagePath": "pages/index/index",\n        "text": "首页",\n        "iconPath": "images/home.png",\n        "selectedIconPath": "images/home-active.png"\n      },\n      {\n        "pagePath": "pages/property/list/index",\n        "text": "找房",\n        "iconPath": "images/search.png",\n        "selectedIconPath": "images/search-active.png"\n      },\n      {\n        "pagePath": "pages/user/profile/index",\n        "text": "我的",\n        "iconPath": "images/user.png",\n        "selectedIconPath": "images/user-active.png"\n      }\n    ]\n  },\n  "window": {\n    "backgroundTextStyle": "light",\n    "navigationBarBackgroundColor": "#FF6B35",\n    "navigationBarTitleText": "县域房产",\n    "navigationBarTextStyle": "white",\n    "backgroundColor": "#f5f5f5"\n  },\n  "style": "v2",\n  "sitemapLocation": "sitemap.json",\n  "permission": {\n    "scope.userLocation": {\n      "desc": "需要获取您的位置信息用于房源定位"\n    }\n  },\n  "requiredBackgroundModes": [\"location\"],\n  "useExtendedLib": {\n    \"weui\": true\n}\n}',
            "app.wxss": "/* 全局样式 */\npage {\n  background-color: #f5f5f5;\n  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;\n}\n\n/* 主题色定义 */\n:root {\n  --primary-color: #FF6B35;\n  --secondary-color: #1E90FF;\n  --text-primary: #333;\n  --text-secondary: #666;\n  --background-color: #f5f5f5;\n  --card-background: #fff;\n  --border-color: #e0e0e0;\n}\n\n/* 通用样式 */\n.container {\n  padding: 16rpx;\n  margin: 0 auto;\n  max-width: 750rpx;\n}\n\n.card {\n  background: var(--card-background);\n  border-radius: 8rpx;\n  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.1);\n  margin-bottom: 16rpx;\n  overflow: hidden;\n}\n\n.btn-primary {\n  background: var(--primary-color);\n  color: white;\n  border: none;\n  padding: 24rpx 48rpx;\n  border-radius: 8rpx;\n  font-size: 32rpx;\n  text-align: center;\n}\n\n.btn-primary:active {\n  background: #e55a2b;\n}\n\n.text-center {\n  text-align: center;\n}\n\n.text-primary {\n  color: var(--primary-color);\n}\n\n.text-secondary {\n  color: var(--text-secondary);\n}\n\n.loading {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  height: 200rpx;\n}\n\n.empty-state {\n  text-align: center;\n  padding: 80rpx 0;\n  color: var(--text-secondary);\n}\n\n/* Flexbox 工具类 */\n.flex {\n  display: flex;\n}\n\n.flex-c {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n}\n\n.flex-sb {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n}\n\n.flex-wrap {\n  flex-wrap: wrap;\n}\n\n.flex-column {\n  flex-direction: column;\n}"\n        },\n        "docs": {\n            "api": {\n                \"README.md\": "# API文档\n\n详细的API文档将在后续开发中逐步完善。\n\n## 文档位置\n- 在线文档：OpenAPI/Swagger UI\n- 本地文档：http://localhost:8000/docs\n- 静态导出：docs/api/index.html\n\n## API版本\n当前版本：v1\nURI前缀：/api/v1/\n\n## 认证方式\nJWT Bearer Token\n\n## 主要接口\n- 用户认证：/api/v1/auth\n- 用户管理：/api/v1/users \n- 房源管理：/api/v1/properties\n- 预约管理：/api/v1/appointments\n- 工具服务：/api/v1/tools\n\n详细接口定义请参考 OpenAPI 文档。"
            },\n            \"DEPLOYMENT.md\": "# 部署文档\n\n## 环境要求\n- Python 3.9+\n- Node.js 16+\n- PostgreSQL 14+\n- Redis 7+\n- Docker & Docker Compose\n\n## 快速部署\n```bash\n# 1. 克隆仓库\ngit clone https://github.com/yourusername/county-real-estate-platform.git\n\n# 2. 配置环境\ncd county-real-estate-platform\ncp .env.example .env\n# 编辑 .env 文件\n\n# 3. 启动服务\ndocker-compose up -d\n\n# 4. 访问服务\n后端API: http://localhost:8000/docs\n小程序: 导入微信开发者工具\n```\n\n详细部署步骤请参考部署指南。",
            \"README.md\": "# 县域房产平台技术文档\n\n## 文档结构\n\ndocs/\n├── api/                    # API接口文档\n├── design/                 # 架构设计文档\n├── deployment/             # 部署指南\n├── development/            # 开发指南\n├── testing/                # 测试文档\n└── user-manuals/           # 用户手册\n\n## 主要文档\n\n### 开发者文档\n- [后端开发指南](development/backend-guide.md)\n- [前端开发指南](development/frontend-guide.md)\n- [测试指南](testing/testing-guide.md)\n- [部署指南](deployment/index.md)\n\n### 架构设计\n- [系统架构](design/architecture.md)\n- [数据库设计](design/database-design.md)\n- [API设计](api/index.md)\n\n### 用户手册\n- [用户使用手册](user-manuals/user-manual.md)\n- [经纪人使用手册](user-manuals/agent-manual.md)\n\n## API文档\n- Swagger UI: http://localhost:8000/docs\n- ReDoc: http://localhost:8000/redoc\n- OpenAPI JSON: http://localhost:8000/openapi.json\n\n## 技术支持\n- 技术问题：GitHub Issues\n- 业务咨询：你的邮箱\n- 文档反馈：GitHub Discussion"
        },\n        ".github": {\n            \"workflows\": {},\n            \"ISSUE_TEMPLATE\": {\n                \"bug_report.md\": "---\nname: Bug报告\nabout: 报告程序的错误\ntitle: \"[BUG] \"\nlabels: bug\nassignees: ''\n\n---\n\n**描述Bug**\n简要清楚地描述问题\n\n**重现步骤**\n1. Go to '...'\n2. Click on '....'\n3. See error\n\n**期望行为**\n描述你期望发生的行为\n\n**截图**\n如果可以，请添加截图\n\n**环境**\n- 操作系统: [e.g. iOS]\n- 微信版本: [e.g. 8.0.31]\n- 小程序版本: [e.g. 1.0.0]\n\n**其他信息**\n添加其他相关信息",\n                \"feature_request.md\": "---\nname: 功能请求\nabout: 建议新功能或改进\ntitle: \"[FEATURE] \"\nlabels: enhancement\nassignees: ''\n\n---\n\n**功能描述**\n简要描述你希望添加的功能\n\n**使用场景**\n描述这个功能的使用场景\n\n**期望效果**\n描述你期望的使用效果\n\n**附加信息**\n添加其他相关信息或截图"
            }\n        }\n    }\n    \n    # 创建.env.example文件\n    env_content = """# 后端配置\nDATABASE_URL=postgresql://xqfc_user:your_password@localhost:5432/xqfc_db\nREDIS_URL=redis://localhost:6379/0\nSECRET_KEY=your-very-secure-secret-key-here\nDEBUG=false\n\n# API配置\nAPI_V1_STR=/api/v1\nPROJECT_NAME=县域房产平台\nVERSION=0.1.0\nDESCRIPTION=县域房产信息平台API\n\n# 安全设置\nACCESS_TOKEN_EXPIRE_MINUTES=10080\nREFRESH_TOKEN_EXPIRE_MINUTES=20160\nPASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15\n\n# 外部服务\nSMS_SERVICE_URL=# 短信服务商API\nSMS_ACCESS_KEY=# 短信服务商访问密钥\nSMS_SECRET_KEY=# 短信服务商密钥\n\n# CORS\nBACKEND_CORS_ORIGINS=[\"http://localhost\", \"http://localhost:8080\", \"https://xqfc.com\"]\n\n# 文件存储\nMAX_FILE_SIZE=10485760  # 10MB\nUPLOAD_DIR=./uploads\nSTATIC_DIR=./static\n\n# 日志\nLOG_LEVEL=INFO\nLOG_FILE=./logs/app.log"""
    \n    return structure, env_content

# 创建目录和文件
def create_files(base_path, structure, env_content):\n    \"\"\"递归创建目录结构\"\"\"\n    \n    base_path = Path(base_path)\n    \n    def create_recursive(current_path, structure_dict):\n        for key, value in structure_dict.items():\n            if isinstance(value, dict):\n                # 创建目录\n                dir_path = current_path / key\n                dir_path.mkdir(parents=True, exist_ok=True)\n                create_recursive(dir_path, value)\n            else:\n                # 创建文件\n                file_path = current_path / key\n                file_path.parent.mkdir(parents=True, exist_ok=True)\n                \n                if value:  # 如果有内容\n                    file_path.write_text(value, encoding='utf-8')\n                else:\n                    file_path.touch()  # 创建空文件\n    \n    create_recursive(base_path, structure)\n    \n    # 创建.env.example文件\n    env_example_path = base_path / ".env.example\"\n    env_example_path.write_text(env_content, encoding='utf-8')\n    \n    # 创建.gitignore文件\n    gitignore_content = """# Python\n__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.Python\nenv/\nvenv/\n.ropeproject/\n.pytest_cache/\n.coverage\nhtmlcov/\ndist/\nbuild/\n*.egg-info/\n\n# Environment\n.env\n.env.local\n.env.production\n\n# Logs\nlogs/\n*.log\n\n# Database\n*.db\n*.sqlite3\npostgresql-data/\nredis-data/\n\n# IDE\n.vscode/\n.idea/\n*.swp\n*.swo\n*~\n\n# macOS\n.DS_Store\n.AppleDouble\n.LSOverride\n\n# Windows\nehthumbs.db\nThumbs.db\n\n# Docker\n.dockerignore\n\n# MiniProgram\nminiprogram/miniprogram_npm/\nminiprogram/node_modules/\nminiprogram/*.log\n\n# Uploads\nuploads/\nstatic/uploads/\n\n# Backup\n*.backup\n*.bak"""\n    \n    gitignore_path = base_path / ".gitignore\"\n    gitignore_path.write_text(gitignore_content, encoding='utf-8')\n\ndef create_github_workflows():\n    \"\"\"创建GitHub Actions工作流文件\"\"\"\n    \n    workflows_dir = Path(\".github/workflows\")\n    workflows_dir.mkdir(parents=True, exist_ok=True)\n    \n    # CI工作流\n    ci_yml = \"\"\"name: CI\n\non:\n  push:\n    branches: [ main, dev ]\n  pull_request:\n    branches: [ main, dev ]\n\nenv:\n  PYTHON_VERSION: 3.9\n  NODE_VERSION: 16\n\njobs:\n  backend-tests:\n    name: Backend Tests\n    runs-on: ubuntu-latest\n    \n    services:\n      postgres:\n        image: postgres:14\n        env:\n          POSTGRES_USER: test_user\n          POSTGRES_PASSWORD: test_password\n          POSTGRES_DB: test_db\n        options: >-\n          --health-cmd pg_isready\n          --health-interval 10s\n          --health-timeout 5s\n          --health-retries 5\n        ports:\n          - 5432:5432\n      \n      redis:\n        image: redis:7-alpine\n        options: >-\n          --health-cmd \\"redis-cli ping\\"\n          --health-interval 10s\n          --health-timeout 5s\n          --health-retries 5\n        ports:\n          - 6379:6379\n    \n    steps:\n    - uses: actions/checkout@v3\n    \n    - name: Set up Python\n      uses: actions/setup-python@v4\n      with:\n        python-version: ${{ env.PYTHON_VERSION }}\n    \n    - name: Install Poetry\n      uses: snok/install-poetry@v1\n      with:\n        version: latest\n        virtualenvs-create: true\n        virtualenvs-in-project: true\n    \n    - name: Install dependencies\n      run: |\n        cd backend\n        poetry install --no-interaction --no-ansi\n    \n    - name: Run backend tests\n      run: |\n        cd backend\n        poetry run pytest tests/ -v --cov=app --cov-report=xml\n      env:\n        DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db\n        REDIS_URL: redis://localhost:6379/0\n        TESTING: true\n    \n    - name: Upload coverage reports\n      uses: codecov/codecov-action@v3\n      with:\n        file: backend/coverage.xml\n        flags: backend\n        name: backend-coverage\n"\"\"\n    \n    (workflows_dir / \"ci.yml\").write_text(ci_yml, encoding='utf-8')\n\ndef create_initial_readme():\n    \"\"\"创建README文件\"\"\"\n    readme_content = \"\"\"# 县域房产信息平台\n\n县域房产信息平台是一个专注于三四线城市且县城地区的房产信息分享平台，通过短视频内容与信息服务 + 看房预约的模式，为返乡置业用户和本地居民提供可信、便捷的房源信息。\n\n## 🎯 项目特色\n\n- **专注县域市场**：填补大平台覆盖空白\n- **短视频营销**：紧跟抖音流量趋势  \n- **轻量级架构**：适合个人开发者独立运维\n- **AI协作开发**：最大化提升开发效率\n\n## 🛠️ 技术栈\n\n### 后端\n- **FastAPI** - 高性能异步Python Web框架\n- **PostgreSQL** - 主数据存储\n- **Redis** - 缓存和会话管理\n- **JWT** - 用户认证\n\n### 前端\n- 微信小程序原生开发\n- WXML/WXSS/JavaScript\n\n### DevOps\n- **Docker** - 容器化部署\n- **GitHub Actions** - CI/CD\n- **Nginx** - 反向代理\n\n## 🚀 快速开始\n\n详细的项目设置和开发指南，请参考 [项目文档](./docs/)。\n\n## 📊 开发进度\n\n查看 [Projects](https://github.com/YOUR_USERNAME/county-real-estate-platform/projects) 了解当前进度。\n\n## 📄 相关文档\n\n- [API文档](./docs/api/)\n- [部署指南](./docs/deployment/)\n- [开发规范](./docs/development/)\n\n## 🤝 贡献指南\n\n请参考 [CONTRIBUTING.md](./CONTRIBUTING.md)\n\n## 📄 许可证\n\n[MIT License](./LICENSE)\n"\"\"\n    \n    readme_path = Path(\"README.md\")\n    readme_path.write_text(readme_content, encoding='utf-8')\n\ndef main():\n    \"\"\"主函数\"\"\"\n    print(\"🚀 开始创建县域房产平台项目结构...\")\n    \n    # 获取项目根目录\n    project_root = Path(\"county-real-estate-platform\")\n    \n    # 创建项目结构\n    structure, env_content = create_project_structure()\n    create_files(project_root, structure, env_content)\n    \n    # 创建GitHub工作流\n    create_github_workflows()\n    \n    # 创建README\n    create_initial_readme()\n    \n    # 创建Git工作流配置\n    create_git_config()\n    \n    print(f\"\\n✅ 项目结构创建完成！\")\n    print(f\"📁 项目路径: {project_root.absolute()}\")\n    print(f\"\\n下一步操作:\")\n    print(f\"1. cd {project_root.name}\")\n    print(f\"2. git init\")\n    print(f\"3. git add .\")\n    print(f\"4. git commit -m 'Initial commit'\")\n    print(f\"5. 设置远程GitHub仓库并推送\")\n    print(f\"\\n🎯 项目特色:\")\n    print(f\"✅ FastAPI后端框架结构\")\n    print(f\"✅ 微信小程序前端结构\")\n    print(f\"✅ Docker容器化配置\")\n    print(f\"✅ GitHub Actions CI/CD\")\n    print(f\"✅ 完整的开发和测试环境\")\n    print(f\"✅ 清晰的项目文档结构\")\n\nif __name__ == \"__main__\":\n    main()\"]