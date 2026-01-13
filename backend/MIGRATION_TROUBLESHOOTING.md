# 数据库迁移问题排查指南

## 当前状态

已修复的问题：
1. ✅ alembic.ini 编码问题 - 已改为纯ASCII
2. ✅ database.py 异步引擎创建问题 - 已添加环境变量控制
3. ✅ appointment.py 模型问题 - 已修复别名冲突

## 下一步操作

### 1. 确保MySQL服务已启动

```bash
# 使用Docker启动MySQL
docker-compose up -d db

# 或者使用本地MySQL服务
# 确保MySQL服务正在运行
```

### 2. 配置数据库连接

编辑 `.env` 文件，确保数据库连接信息正确：

```env
DATABASE_URL=mysql+asyncmy://用户名:密码@localhost:3306/数据库名
```

例如：
```env
DATABASE_URL=mysql+asyncmy://root:your_password@localhost:3306/xqfc_db
```

### 3. 创建数据库（如果不存在）

```sql
-- 连接到MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE xqfc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户（如果需要）
CREATE USER 'xqfc_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON xqfc_db.* TO 'xqfc_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 创建迁移文件（离线模式）

如果数据库连接有问题，可以先使用离线模式创建迁移文件：

```bash
# 离线模式创建迁移（不需要连接数据库）
alembic revision --autogenerate -m "Create complete database schema" --sql
```

### 5. 执行迁移

```bash
# 确保数据库连接正确后
alembic upgrade head
```

## 常见错误

### 错误1: Access denied
**原因**: 数据库用户名或密码错误
**解决**: 检查.env文件中的DATABASE_URL配置

### 错误2: Unknown database
**原因**: 数据库不存在
**解决**: 先创建数据库（见步骤3）

### 错误3: ModuleNotFoundError: asyncmy
**原因**: 依赖未安装
**解决**: `pip install -r requirements.txt`

## 验证迁移

迁移成功后，可以验证表结构：

```sql
USE xqfc_db;
SHOW TABLES;

-- 查看某个表结构
DESCRIBE users;
DESCRIBE properties;
```
