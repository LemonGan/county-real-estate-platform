# ==========================================
# 县域房产平台 - 一键生产部署脚本
# 在服务器上执行: bash deploy.sh
# ==========================================

set -e

PROJECT_DIR="/www/wwwroot/county-real-estate"
VENV_DIR="$PROJECT_DIR/venv"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "=========================================="
echo "  县域房产平台 - 生产部署"
echo "  服务器: 8.138.129.142"
echo "=========================================="

# 1. 创建目录
echo "[1/6] 创建目录..."
mkdir -p $PROJECT_DIR/uploads
mkdir -p $PROJECT_DIR/static
mkdir -p $PROJECT_DIR/logs
echo "  OK"

# 2. 配置 Python 虚拟环境
echo "[2/6] 配置虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate
pip install --upgrade pip -q
echo "  OK"

# 3. 安装依赖
echo "[3/6] 安装Python依赖..."
cd $BACKEND_DIR
pip install -r requirements.txt -q
echo "  OK"

# 4. 配置环境变量
echo "[4/6] 检查 .env 配置..."
if [ ! -f "$BACKEND_DIR/.env" ]; then
    cp $PROJECT_DIR/deploy/production.env $BACKEND_DIR/.env
    echo "  ⚠️  已复制模板 .env，请手动修改数据库密码和微信配置！"
    echo "  编辑: vi $BACKEND_DIR/.env"
    exit 1
fi
echo "  OK"

# 5. 初始化数据库
echo "[5/6] 初始化数据库表..."
python -c "
import asyncio
from app.core.database import engine, Base
from app.models import *
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('  数据库表创建完成')
asyncio.run(init())
"
echo "  OK"

# 6. 重启服务
echo "[6/6] 重启服务..."
supervisorctl restart county_real_estate
echo "  OK"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "验证命令:"
echo "  curl http://127.0.0.1:8000/health"
echo "  curl http://8.138.129.142/api/v1/health"
echo ""
echo "查看日志:"
echo "  tail -f $PROJECT_DIR/logs/app.log"
echo ""
