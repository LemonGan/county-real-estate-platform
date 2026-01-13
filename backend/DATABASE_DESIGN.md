# 县域房产平台数据库设计方案

## 📋 设计目标

本数据库设计旨在支持一个专注县域房产市场的信息分享平台，结合短视频营销和AI推荐算法，为返乡置业用户、本地改善用户和投资用户提供专业的房产信息服务。

## 🎯 设计原则

### 1. 产品导向设计
- **用户画像支持**: 针对返乡置业、本地改善、投资用户三类核心用户的行为特征设计数据模型
- **县域特色**: 专门设计乡镇层级地理位置、学区信息、区域发展等县域特色字段
- **短视频整合**: 完整支持短视频内容创作、分发、推荐的全链路数据需求

### 2. 性能优先策略
- **高并发支持**: 设计支持1000并发用户的索引策略和查询优化
- **大数据分区**: 针对用户行为、房源数据等大数据量表进行分区设计
- **缓存友好**: 数据模型设计考虑Redis缓存策略，减少重复计算

### 3. 扩展性考虑
- **模块化结构**: 表结构分层设计，便于功能模块独立扩展
- **城市扩展**: 四级地理位置结构支持多县域快速接入
- **状态管理**: 统一的枚举值管理支持业务状态灵活扩展

## 🗄️ 核心表结构设计

### 用户管理模块

#### users - 用户主体表
```sql
-- 用户基础信息，支持微信登录、角色权限、地理位置管理
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    openid VARCHAR(100) UNIQUE,           -- 微信openid
    unionid VARCHAR(100) UNIQUE,          -- 微信unionid
    mobile VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(255),

    -- 基本信息
    nickname VARCHAR(50),
    avatar_url TEXT,
    real_name VARCHAR(50),
    id_card VARCHAR(18),                  -- 实名认证
    gender SMALLINT CHECK (gender IN (0, 1, 2)),

    -- 县域特色 - 地理位置
    current_city VARCHAR(50),             -- 当前城市
    hometown_city VARCHAR(50),            -- 家乡城市 (返乡用户关键字段)
    preferred_districts TEXT[],           -- 偏好区域数组

    -- 角色权限
    user_type SMALLINT CHECK (user_type IN (1, 2, 3)),
    is_verified BOOLEAN DEFAULT FALSE,
    is_agent BOOLEAN DEFAULT FALSE,
    agent_license VARCHAR(50),

    -- 微信数据
    session_key VARCHAR(100),
    subscribe_scene VARCHAR(100),
    subscribe_time TIMESTAMP,

    -- 营销分析
    source_channel VARCHAR(50),
    utm_campaign VARCHAR(100),
    registration_ip INET,

    -- 状态管理
    status SMALLINT DEFAULT 1,
    last_login_at TIMESTAMP,
    last_login_ip INET,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);
```

#### user_preferences - 用户偏好表
```sql
-- 用户个性化偏好，用于AI推荐算法
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 购房预算偏好
    budget_min INTEGER,                   -- 最小预算(万元)
    budget_max INTEGER,                   -- 最大预算(万元)
    area_min INTEGER,                     -- 最小面积(㎡)
    area_max INTEGER,                     -- 最大面积(㎡)
    preferred_property_types SMALLINT[], -- 偏好户型类型
    preferred_locations TEXT[],           -- 偏好位置
    has_children BOOLEAN,                 -- 是否有孩子(学区需求)

    -- 推荐算法权重配置
    price_weight DECIMAL(3,2) DEFAULT 0.3,
    location_weight DECIMAL(3,2) DEFAULT 0.3,
    school_weight DECIMAL(3,2) DEFAULT 0.2,
    transport_weight DECIMAL(3,2) DEFAULT 0.2,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### user_behaviors - 用户行为轨迹表
```sql
-- 用户行为数据，短视频推荐和AI算法关键数据源
CREATE TABLE user_behaviors (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    behavior_type SMALLINT CHECK (behavior_type IN (1,2,3,4,5)),
    -- 1:浏览, 2:收藏, 3:分享, 4:电话咨询, 5:看房预约
    target_type SMALLINT CHECK (target_type IN (1,2,3)),
    -- 1:房源, 2:视频, 3:文章
    target_id INTEGER,
    duration INTEGER,                     -- 停留时长(秒)
    action_data JSONB,                    -- 详细行为数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_behaviors_user_target ON user_behaviors(user_id, target_type, target_id);
CREATE INDEX idx_user_behaviors_created ON user_behaviors(created_at);
```

### 房源管理模块

#### properties - 房源信息主表
```sql
-- 房源核心信息，包含县域市场特色字段
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    property_no VARCHAR(20) UNIQUE,        -- 房源编号
    agent_id INTEGER NOT NULL REFERENCES users(id),

    -- 基本信息
    title VARCHAR(200) NOT NULL,
    description TEXT,
    property_type SMALLINT NOT NULL,       -- 1:住宅, 2:商铺, 3:写字楼, 4:别墅
    transaction_type SMALLINT NOT NULL,    -- 1:出售, 2:出租

    -- 县域特色 - 四级地理位置
    province VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    district VARCHAR(50) NOT NULL,         -- 区/县
    town VARCHAR(50),                      -- 镇/街道
    village VARCHAR(50),                   -- 村/社区
    detail_address VARCHAR(200),
    longitude DECIMAL(10,7),
    latitude DECIMAL(10,7),

    -- 价格与面积
    total_price INTEGER,                   -- 总价
    unit_price INTEGER,                    -- 单价(元/㎡)
    area DECIMAL(6,2),                     -- 建筑面积

    -- 房型结构
    room_count SMALLINT,
    hall_count SMALLINT,
    bathroom_count SMALLINT,
    floor_info VARCHAR(50),
    total_floors SMALLINT,
    build_year SMALLINT,
    decoration_type SMALLINT,

    -- 县域特色配置
    school_district VARCHAR(100),          -- 学区信息(返乡用户重点关注)
    transportation TEXT[],                 -- 交通配套
    surrounding_facilities JSONB,          -- 周边设施详情
    property_rights_years SMALLINT,        -- 产权年限
    down_payment_ratio DECIMAL(3,1),       -- 首付比例

    -- 多媒体资源
    cover_image_url TEXT,
    video_urls TEXT[],                     -- 视频链接数组
    vr_url TEXT,                           -- VR看房链接
    has_vr BOOLEAN DEFAULT FALSE,
    has_video BOOLEAN DEFAULT FALSE,

    -- 状态管理
    status SMALLINT DEFAULT 1,             -- 1:在售, 2:已售, 3:下架
    audit_status SMALLINT DEFAULT 0,       -- 审核状态
    verify_status BOOLEAN DEFAULT FALSE,   -- 真实性验证

    -- 营销统计
    view_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    inquiry_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,

    -- SEO与标签
    tags TEXT[],
    keywords VARCHAR(500),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);
```

#### property_images - 房源图片表
```sql
-- 房源多媒体资源管理
CREATE TABLE property_images (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    thumbnail_url TEXT,
    image_type SMALLINT DEFAULT 0,         -- 0:普通, 1:客厅, 2:卧室, 3:厨房
    sort_order INTEGER DEFAULT 0,
    is_cover BOOLEAN DEFAULT FALSE,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### property_favorites - 用户收藏表
```sql
-- 用户收藏房源关系
CREATE TABLE property_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    property_id INTEGER NOT NULL REFERENCES properties(id),
    price_alert BOOLEAN DEFAULT FALSE,     -- 价格变动提醒
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, property_id)
);
```

### 看房预约模块

#### appointments - 看房预约表
```sql
-- 看房预约核心业务流程
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    appointment_no VARCHAR(30) UNIQUE,     -- 预约编号
    user_id INTEGER NOT NULL REFERENCES users(id),
    property_id INTEGER NOT NULL REFERENCES properties(id),
    agent_id INTEGER NOT NULL REFERENCES users(id),

    -- 预约详情
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    appointment_type SMALLINT DEFAULT 1,   -- 1:实地看房, 2:视频看房, 3:VR看房
    participants_count SMALLINT DEFAULT 2,

    -- 联系信息
    contact_name VARCHAR(50) NOT NULL,
    contact_mobile VARCHAR(20) NOT NULL,
    contact_wechat VARCHAR(50),
    special_requirements TEXT,

    -- 状态工作流
    status SMALLINT DEFAULT 1,             -- 0:已取消, 1:待确认, 2:已确认, 3:已完成
    confirmation_status SMALLINT DEFAULT 0,
    cancel_reason TEXT,
    cancel_time TIMESTAMP,

    -- 看房反馈
    feedback_score SMALLINT,               -- 满意度评分1-5
    feedback_comment TEXT,
    is_interested BOOLEAN,
    next_followup TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

#### agent_availability - 经纪人时间表
```sql
-- 经纪人可用时间，支持预约时间管理
CREATE TABLE agent_availability (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES users(id),
    available_date DATE NOT NULL,
    available_slots JSONB,                 -- 可用时段数组
    is_fully_booked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, available_date)
);
```

### 短视频与内容模块

#### short_videos - 短视频内容表
```sql
-- 短视频内容管理，支持多平台分发
CREATE TABLE short_videos (
    id SERIAL PRIMARY KEY,
    video_no VARCHAR(30) UNIQUE,           -- 视频编号
    creator_id INTEGER NOT NULL REFERENCES users(id),
    property_id INTEGER REFERENCES properties(id),

    title VARCHAR(200) NOT NULL,
    description TEXT,
    video_url TEXT NOT NULL,
    cover_image_url TEXT,
    video_duration INTEGER,
    file_size INTEGER,

    -- 平台分发
    platform_tags TEXT[],                  -- 抖音、快手、小红书标签
    is_published BOOLEAN DEFAULT FALSE,
    publish_time TIMESTAMP,

    -- 统计信息
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,

    -- 审核状态
    review_status SMALLINT DEFAULT 0,
    review_note TEXT,
    reviewer_id INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);
```

#### video_recommendations - 视频推荐算法表
```sql
-- AI推荐算法计算结果存储
CREATE TABLE video_recommendations (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    video_id INTEGER NOT NULL REFERENCES short_videos(id),

    -- 推荐算法权重
    base_score DECIMAL(5,4),               -- 基础得分
    user_preference_score DECIMAL(5,4),    -- 用户偏好得分
    location_score DECIMAL(5,4),           -- 地理位置得分
    recency_score DECIMAL(5,4),            -- 时效性得分
    engagement_score DECIMAL(5,4),         -- 互动率得分
    final_score DECIMAL(6,4),              -- 最终得分

    -- 推荐状态追踪
    is_shown BOOLEAN DEFAULT FALSE,
    shown_at TIMESTAMP,
    clicked BOOLEAN DEFAULT FALSE,
    clicked_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_video_rec_user_score ON video_recommendations(user_id, final_score DESC);
```

## 🚀 性能优化策略

### 索引优化

```sql
-- 用户相关索引
CREATE INDEX idx_users_location ON users(current_city, hometown_city) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_mobile ON users(mobile) WHERE deleted_at IS NULL;

-- 房源搜索优化 (核心业务)
CREATE INDEX idx_properties_location ON properties(city, district, town) WHERE status = 1;
CREATE INDEX idx_properties_price ON properties(total_price) WHERE status = 1;
CREATE INDEX idx_properties_price_area ON properties(total_price, area) WHERE status = 1;
CREATE INDEX idx_properties_advanced ON properties(
    city, district, property_type, transaction_type,
    total_price, area, status
);

-- 预约查询优化
CREATE INDEX idx_appointments_composite ON appointments(user_id, property_id, status, appointment_date);
CREATE INDEX idx_appointments_time_range ON appointments(appointment_date, appointment_time) WHERE status IN (1, 2, 3);

-- 推荐算法优化
CREATE INDEX idx_video_rec_realtime ON video_recommendations(user_id, final_score DESC) WHERE is_shown = FALSE;
CREATE INDEX idx_user_behaviors_user_type ON user_behaviors(user_id, behavior_type, target_type);
```

### 分区策略

```sql
-- 用户行为表分区 - 按时间分区应对大数据量
CREATE TABLE user_behaviors_partitioned (LIKE user_behaviors INCLUDING ALL)
PARTITION BY RANGE (created_at);

-- 按月份创建分区表
CREATE TABLE user_behaviors_2024_01 PARTITION OF user_behaviors_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 预约表按状态分区 - 提升活跃查询性能
CREATE TABLE appointments_partitioned (LIKE appointments INCLUDING ALL)
PARTITION BY LIST (status);

CREATE TABLE appointments_active PARTITION OF appointments_partitioned
    FOR VALUES IN (1, 2, 3);     -- 活跃预约
CREATE TABLE appointments_inactive PARTITION OF appointments_partitioned
    FOR VALUES IN (0, 4);        -- 取消/完成预约
```

### 缓存策略设计

```python
# Redis缓存键设计
PROPERTY_DETAIL_CACHE = "property:{property_id}:detail"  # TTL: 30分钟
PROPERTY_SEARCH_CACHE = "properties:search:{hash}"      # TTL: 10分钟
USER_PREFERENCE_CACHE = "user:{user_id}:preferences"    # TTL: 1小时
VIDEO_RECOMMENDATION_CACHE = "video:rec:{user_id}"     # TTL: 1小时
APPOINTMENT_CACHE = "appointment:{appointment_id}"     # TTL: 5分钟

# 预聚合统计表
CREATE TABLE property_statistics (
    property_id INTEGER PRIMARY KEY REFERENCES properties(id),
    total_views INTEGER DEFAULT 0,
    total_inquiries INTEGER DEFAULT 0,
    total_appointments INTEGER DEFAULT 0,
    avg_daily_views DECIMAL(10,2) DEFAULT 0,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_interest_statistics (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    viewed_properties INTEGER DEFAULT 0,
    favorited_properties INTEGER DEFAULT 0,
    total_appointments INTEGER DEFAULT 0,
    last_active TIMESTAMP,
    property_preferences JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📊 性能指标与监控

### 查询性能目标

| 查询类型 | 预期响应时间 | 并发支持 | 优化策略 |
|---------|-------------|----------|----------|
| 房源列表搜索 | `<500ms` | 500并发 | 复合索引 + Redis缓存 |
| 单用户推荐列表 | `<200ms` | 1000并发 | 预计算 + 索引优化 |
| 用户行为写入 | `<50ms` | 2000并发 | 分区表 + 批量写入 |
| 预约冲突检测 | `<100ms` | 500并发 | 时间索引 + constraint |

### 监控与告警

```sql
-- 系统日志表
CREATE TABLE system_logs (
    id BIGSERIAL PRIMARY KEY,
    log_level SMALLINT NOT NULL,
    module VARCHAR(50),
    operation VARCHAR(100),
    user_id INTEGER REFERENCES users(id),
    request_id VARCHAR(50),
    details JSONB,
    error_stack TEXT,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 配置监控告警阈值
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入监控配置示例
INSERT INTO system_configs (config_key, config_value, description) VALUES
('api_performance_thresholds', '{"warning_ms": 500, "critical_ms": 1000}', 'API性能告警阈值'),
('concurrent_user_limits', '{"max_concurrent": 1000, "burst_limit": 1500}', '并发用户限制'),
('cache_ttl_settings', '{"property_detail": 1800, "search_results": 600, "user_session": 86400}', '缓存TTL设置');
```

## 🔗 系统整体数据流

### 用户注册与登录流程
```
微信授权 → 获取openid/unionid → 创建用户记录 → 初始化用户偏好 → 生成JWT Token → 返回用户信息
```

### 房源发布与管理流程
```
经纪人创建房源 → 上传图片/视频 → 提交审核 → 审核通过 → 生成搜索索引 → 分发到推荐系统
```

### 看房预约流程
```
用户浏览房源 → 选择看房时间 → 检查经纪人可用性 → 创建预约 → 经纪人确认 → 发送通知 → 完成看房反馈
```

### 短视频推荐算法流程
```
用户行为收集 → 偏好分析计算 → 内容相似度匹配 → 地理位置权重 → 生成推荐列表 → 缓存结果 → 呈现给用户
```

## 🎯 与现有后端架构的集成方案

### 模型文件更新建议

```python
# app/models/user.py - 扩展现有模型
class User(Base):
    __tablename__ = "users"
    # 保持现有字段，新增县域特色字段
    current_city = Column(String(50), comment="当前所在城市")
    hometown_city = Column(String(50), comment="家乡城市")
    preferred_districts = Column(ARRAY(String), comment="偏好区域")
    is_verified = Column(Boolean, default=False, comment="实名认证状态")
    agent_license = Column(String(50), comment="经纪人执业证号")

# app/models/property.py - 新增完整模型
class Property(Base):
    __tablename__ = "properties"
    # 完整的房源模型定义包含县域特色字段
    town = Column(String(50), comment="镇/街道")
    village = Column(String(50), comment="村/社区")
    school_district = Column(String(100), comment="学区信息")
    transportation = Column(ARRAY(String), comment="交通配套")
    down_payment_ratio = Column(Numeric(3,1), comment="首付比例")
```

### 数据库迁移执行

```bash
# 1. 创建新的迁移文件
alembic revision --autogenerate -m "Add county real estate complete schema"

# 2. 执行迁移（测试环境）
alembic upgrade head

# 3. 迁移验证脚本
python scripts/validate_migration.py

# 4. 初始化基础数据
python scripts/init_county_data.py
```

## 📈 后续扩展规划

### 第一阶段：基础功能验证 (当前)
- 完成核心表结构设计与实施
- 验证基础API与数据模型的兼容性
- 进行初步性能测试与调优

### 第二阶段：高级功能开发
- 实施AI推荐算法相关的数据结构设计
- 完善短视频内容管理相关表
- 增加复杂查询性能优化

### 第三阶段：规模化扩展
- 实施数据分区策略
- 增加跨区域数据统一管理
- 完善监控告警体系

## 📝 注意事项与最佳实践

### 数据安全
1. **敏感数据加密**：手机号、身份证等敏感信息考虑加密存储
2. **访问权限控制**：不同角色用户的数据访问权限管理
3. **审计日志**：关键业务操作需要完整审计追踪

### 性能维护
1. **定期分析表**：`ANALYZE`重要业务表，确保查询优化器准确性
2. **索引重建**：定期检查并重建使用频率高的索引
3. **表空间管理**：大表分区管理，定期归档历史数据

### 运维监控
1. **慢查询监控**：开启并定期检查慢查询日志
2. **连接池监控**：监控数据库连接池使用情况
3. **存储空间监控**：预警数据库存储空间使用率

---

**总结**: 本数据库设计充分考虑了县域房产平台的特殊需求，平衡了功能完整性与实施复杂度，既能支持MVP快速验证，又为后续规模化扩展留足空间。设计特别关注短视频内容推荐和AI算法支持，通过合理的表结构设计和索引优化策略，确保系统在高并发场景下的稳定性能表现。