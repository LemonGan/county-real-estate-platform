# 数据库迁移指南

## 创建迁移文件

在安装完所有依赖后，执行以下命令创建迁移文件：

```bash
# 确保在backend目录下
cd backend

# 创建迁移文件
alembic revision --autogenerate -m "Create complete database schema for county real estate platform"

# 检查生成的迁移文件
# 文件位置：alembic/versions/xxxx_create_complete_database_schema.py
```

## 执行迁移

```bash
# 执行迁移（创建所有表）
alembic upgrade head

# 如果需要回滚
alembic downgrade -1
```

## 注意事项

1. **首次迁移前**：确保MySQL数据库已创建
2. **环境变量**：确保.env文件中的DATABASE_URL配置正确
3. **依赖安装**：确保已安装所有依赖，特别是asyncmy和pymysql

## 数据库表结构

根据DATABASE_DESIGN.md设计，将创建以下表：

### 用户相关
- users - 用户主体表
- user_preferences - 用户偏好表
- user_behaviors - 用户行为轨迹表

### 房源相关
- properties - 房源信息主表
- property_images - 房源图片表
- property_favorites - 用户收藏表

### 预约相关
- appointments - 看房预约表
- agent_availability - 经纪人时间表

### 短视频相关
- short_videos - 短视频内容表
- video_recommendations - 视频推荐算法表

## 验证迁移

迁移完成后，可以连接数据库验证：

```sql
-- 查看所有表
SHOW TABLES;

-- 查看某个表结构
DESCRIBE users;
DESCRIBE properties;
```
