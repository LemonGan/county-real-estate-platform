# 县域房产平台部署指南

## 服务器信息

- **操作系统**: CentOS 7.9 64位
- **配置**: 2核(vCPU) 2GiB
- **IP地址**: 8.138.129.142
- **管理面板**: 宝塔面板

---

## 部署架构

```
                        ┌─────────────┐
                        │   Nginx     │ (80/443)
                        │  反向代理    │
                        └──────┬──────┘
                               │
                        ┌──────▼──────┐
                        │  FastAPI    │ (8000)
                        │  后端服务    │
                        └──────┬──────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
        ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼─────┐
        │    MySQL     │ │  Redis   │ │  本地文件  │
        │   (3306)     │ │  (6379)  │ │  /uploads │
        └──────────────┘ └──────────┘ └───────────┘
```

---

## 部署步骤

### 第一步：安装宝塔面板

如果尚未安装宝塔面板，请执行：

```bash
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh
```

安装完成后，访问 `http://8.138.129.142:8888` 登录宝塔面板。

### 第二步：在宝塔面板中安装环境

登录宝塔面板后，进入 **软件商店**，安装以下软件：

| 软件 | 版本 | 用途 |
|------|------|------|
| Nginx | 1.20+ | Web服务器和反向代理 |
| MySQL | 5.7+ | 数据库 |
| Redis | 6.0+ | 缓存 |
| Python 3 | 3.8+ | 运行环境 |
| Supervisor | - | 进程管理 |

### 第三步：上传项目代码

1. 在宝塔面板中，进入 **文件** 管理
2. 创建目录 `/www/wwwroot/county-real-estate`
3. 将以下文件/目录上传到服务器：

```
/www/wwwroot/county-real-estate/
├── backend/          # 后端代码
│   ├── app/
│   ├── requirements.txt
│   └── ...
├── miniprogram/      # 小程序代码（供开发使用）
├── deploy/           # 部署脚本
│   ├── production.env
│   ├── nginx.conf
│   └── supervisor.conf
├── uploads/          # 上传文件目录（自动创建）
└── logs/             # 日志目录（自动创建）
```

### 第四步：创建MySQL数据库

在宝塔面板中：

1. 进入 **数据库** 菜单
2. 创建数据库：
   - 数据库名：`xqfc_db`
   - 用户名：`xqfc_user`
   - 密码：[设置强密码]
   - 字符集：`utf8mb4`

### 第五步：创建Python虚拟环境

通过SSH连接服务器，执行：

```bash
# 进入项目目录
cd /www/wwwroot/county-real-estate

# 创建Python 3.8虚拟环境
python3.8 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 第六步：安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

如果安装失败，可能需要安装一些系统依赖：

```bash
yum install -y python38-devel mysql-devel openldap-devel
```

### 第七步：配置环境变量

创建 `.env` 文件：

```bash
cd /www/wwwroot/county-real-estate/backend
vi .env
```

复制以下内容（修改数据库密码等配置）：

```env
# 数据库配置
DATABASE_URL=mysql+asyncmy://xqfc_user:your_password@localhost:3306/xqfc_db

# Redis配置
REDIS_URL=redis://:your_redis_password@localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key-change-in-production-min-32-chars

# 调试模式
DEBUG=false

# CORS配置
BACKEND_CORS_ORIGINS=http://8.138.129.142,https://8.138.129.142

# 文件上传配置
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/www/wwwroot/county-real-estate/uploads
STATIC_DIR=/www/wwwroot/county-real-estate/static

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/www/wwwroot/county-real-estate/logs/app.log

# 微信小程序配置
WECHAT_APPID=
WECHAT_SECRET=
```

### 第八步：初始化数据库

```bash
cd /www/wwwroot/county-real-estate/backend
source /www/wwwroot/county-real-estate/venv/bin/activate

# 初始化数据库表
python38 -c "
import asyncio
from app.core.database import engine
from app.models import Base
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"
```

### 第九步：配置Nginx

在宝塔面板中：

1. 进入 **网站** 菜单
2. 添加站点：
   - 域名：`8.138.129.142`
   - 根目录：`/www/wwwroot/county-real-estate`
   - PHP版本：纯静态

3. 点击站点设置，进入 **配置文件**
4. 将 `deploy/nginx.conf` 的内容复制进去
5. 保存并重载配置

### 第十步：配置Supervisor

1. 在宝塔面板中，进入 **软件商店** -> **Supervisor** -> **设置**
2. 添加守护进程：

```
名称: county_real_estate
目录: /www/wwwroot/county-real-estate/backend
命令: /www/wwwroot/county-real-estate/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
用户: root
自动启动: 是
```

3. 启动进程

### 第十一步：配置防火墙

在宝塔面板中，进入 **安全** 菜单，放行以下端口：

- 80 (HTTP)
- 443 (HTTPS)
- 8000 (后端API，可选择性开放)

同时在阿里云控制台的安全组中放行这些端口。

---

## 验证部署

### 1. 检查服务状态

```bash
# 检查supervisor进程
supervisorctl status county_real_estate

# 查看应用日志
tail -f /www/wwwroot/county-real-estate/logs/app.log

# 检查端口监听
netstat -tuln | grep 8000
```

### 2. 测试API接口

```bash
# 健康检查
curl http://8.138.129.142/health

# API文档
curl http://8.138.129.142/docs
```

---

## 常用管理命令

### 服务管理

```bash
# 启动服务
supervisorctl start county_real_estate

# 停止服务
supervisorctl stop county_real_estate

# 重启服务
supervisorctl restart county_real_estate

# 查看日志
supervisorctl tail county_real_estate

# 查看状态
supervisorctl status county_real_estate
```

### 日志查看

```bash
# 应用日志
tail -f /www/wwwroot/county-real-estate/logs/app.log

# Nginx访问日志
tail -f /www/wwwlogs/county_real_estate_access.log

# Nginx错误日志
tail -f /www/wwwlogs/county_real_estate_error.log
```

### 数据库备份

```bash
# 备份数据库
mysqldump -u xqfc_user -p xqfc_db > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u xqfc_user -p xqfc_db < backup_20240113.sql
```

---

## 微信小程序配置

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 获取小程序的 AppID 和 AppSecret
3. 在服务器上修改 `.env` 文件：

```env
WECHAT_APPID=your_app_id
WECHAT_SECRET=your_app_secret
```

4. 在小程序管理后台配置服务器域名：
   - request合法域名：`https://8.138.129.142`
   - uploadFile合法域名：`https://8.138.129.142`
   - downloadFile合法域名：`https://8.138.129.142`

---

## HTTPS配置（推荐）

生产环境建议配置HTTPS证书：

1. 在宝塔面板中，进入 **网站** -> **设置** -> **SSL**
2. 选择 **Let's Encrypt** 免费证书
3. 点击申请

或使用已有证书，上传证书文件后启用。

---

## 故障排查

### 问题1：服务无法启动

```bash
# 查看详细错误
supervisorctl tail county_real_estate

# 检查端口占用
netstat -tuln | grep 8000
```

### 问题2：数据库连接失败

检查 `.env` 文件中的数据库配置是否正确，测试连接：

```bash
mysql -u xqfc_user -p -h localhost xqfc_db
```

### 问题3：API返回502

检查后端服务是否正常运行：

```bash
curl http://127.0.0.1:8000/health
```

---

## 联系支持

如遇到部署问题，请提供以下信息：

1. 错误日志：`/www/wwwroot/county-real-estate/logs/app.log`
2. Nginx错误日志：`/www/wwwlogs/county_real_estate_error.log`
3. 服务状态：`supervisorctl status county_real_estate`
