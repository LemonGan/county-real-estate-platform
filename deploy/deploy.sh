#!/bin/bash

# 县域房产平台部署脚本
# 适用于 CentOS 7.9 + 宝塔面板

set -e

echo "========================================="
echo "  县域房产平台 - 自动部署脚本"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目配置
PROJECT_NAME="county-real-estate"
PROJECT_DIR="/www/wwwroot/$PROJECT_NAME"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
UPLOAD_DIR="$PROJECT_DIR/uploads"

# MySQL配置
DB_NAME="xqfc_db"
DB_USER="xqfc_user"
DB_PASS=$(openssl rand -base64 16)

# Redis配置
REDIS_PASS=$(openssl rand -base64 16)

# 生成随机密钥
SECRET_KEY=$(openssl rand -base64 32)

echo -e "${GREEN}1. 检查系统环境...${NC}"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用 root 用户运行此脚本${NC}"
    exit 1
fi

# 检查系统版本
if [ ! -f /etc/redhat-release ]; then
    echo -e "${RED}此脚本仅适用于 CentOS 系统${NC}"
    exit 1
fi

echo -e "${GREEN}2. 安装系统依赖...${NC}"

# 安装EPEL源
if ! rpm -qa | grep -q epel-release; then
    yum install -y epel-release
fi

# 安装依赖
yum install -y python38 python38-devel python38-pip git nginx supervisor mysql redis

echo -e "${GREEN}3. 创建项目目录...${NC}"

mkdir -p $PROJECT_DIR
mkdir -p $LOG_DIR
mkdir -p $UPLOAD_DIR
mkdir -p /www/wwwlogs

echo -e "${GREEN}4. 配置MySQL数据库...${NC}"

# 启动MySQL
systemctl start mysqld
systemctl enable mysqld

# 创建数据库和用户
mysql -u root -p$(cat /etc/mysql.cnf | grep password | head -1 | awk '{print $3}') <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

echo -e "${GREEN}5. 配置Redis...${NC}"

# 设置Redis密码
if [ -f /etc/redis.conf ]; then
    sed -i "s/# requirepass foobared/requirepass $REDIS_PASS/" /etc/redis.conf
    sed -i "s/bind 127.0.0.1/bind 0.0.0.0/" /etc/redis.conf
fi

# 启动Redis
systemctl start redis
systemctl enable redis

echo -e "${GREEN}6. 创建Python虚拟环境...${NC}"

cd $PROJECT_DIR
python38 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# 升级pip
pip install --upgrade pip

echo -e "${GREEN}7. 上传项目代码...${NC}"
echo -e "${YELLOW}请将项目代码上传到: $BACKEND_DIR${NC}"
echo -e "${YELLOW}然后按回车继续...${NC}"
read

echo -e "${GREEN}8. 安装Python依赖...${NC}"

cd $BACKEND_DIR
pip install -r requirements.txt

echo -e "${GREEN}9. 创建环境配置文件...${NC}"

cat > $BACKEND_DIR/.env <<EOF
# 数据库配置
DATABASE_URL=mysql+asyncmy://$DB_USER:$DB_PASS@localhost:3306/$DB_NAME

# Redis配置
REDIS_URL=redis://:$REDIS_PASS@localhost:6379/0

# 安全配置
SECRET_KEY=$SECRET_KEY

# 调试模式
DEBUG=false

# CORS配置
BACKEND_CORS_ORIGINS=http://8.138.129.142,https://8.138.129.142

# 文件上传配置
MAX_FILE_SIZE=10485760
UPLOAD_DIR=$UPLOAD_DIR
STATIC_DIR=$PROJECT_DIR/static

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/app.log

# 微信小程序配置
WECHAT_APPID=
WECHAT_SECRET=
EOF

echo -e "${GREEN}10. 初始化数据库...${NC}"

# 初始化数据库表
cd $BACKEND_DIR
python38 -c "
import asyncio
from app.core.database import engine
from app.models import Base
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"

echo -e "${GREEN}11. 配置Supervisor...${NC}"

# 复制supervisor配置
cp $BACKEND_DIR/../deploy/supervisor.conf /etc/supervisord.d/county_real_estate.conf

# 重新加载supervisor
supervisorctl reread
supervisorctl update

echo -e "${GREEN}12. 配置Nginx...${NC}"

# 复制nginx配置
cp $BACKEND_DIR/../deploy/nginx.conf /www/server/panel/vhost/nginx/county_real_estate.conf

# 测试nginx配置
nginx -t

# 重载nginx
nginx -s reload

echo -e "${GREEN}13. 启动应用服务...${NC}"

# 启动应用
supervisorctl start county_real_estate

echo -e "${GREEN}14. 配置防火墙...${NC}"

# 开放端口
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload
fi

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "数据库信息:"
echo "  数据库名: $DB_NAME"
echo "  数据库用户: $DB_USER"
echo "  数据库密码: $DB_PASS"
echo ""
echo "Redis信息:"
echo "  Redis密码: $REDIS_PASS"
echo ""
echo "访问地址:"
echo "  API地址: http://8.138.129.142/api/"
echo "  API文档: http://8.138.129.142/docs"
echo "  健康检查: http://8.138.129.142/health"
echo ""
echo -e "${YELLOW}重要信息请妥善保存！${NC}"
echo ""
echo "管理命令:"
echo "  查看日志: supervisorctl tail county_real_estate"
echo "  重启服务: supervisorctl restart county_real_estate"
echo "  停止服务: supervisorctl stop county_real_estate"
echo ""
