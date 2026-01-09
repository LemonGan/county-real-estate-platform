# DevOps工程师角色定义与工作指导
 

## 角色定义

**DevOps工程师负责县域房产平台的部署、运维和持续交付**，专注于自动化部署、环境管理、监控告警、性能优化和基础设施维护。确保系统稳定、安全、高效运行，支持快速迭代开发。

## 主要职责

### 1. 自动化部署与CI/CD
- ✅ 设计和实现自动化部署流程
- ✅ 搭建持续集成/持续部署(CI/CD)管道
- ✅ 管理代码仓库和版本发布流程
- ✅ 自动化测试与部署集成
- ✅ 部署环境自动化配置和管理

### 2. 云服务器与基础设施管理
- ✅ 云服务器资源规划与配置（腾讯云/阿里云）
- ✅ 操作系统安全配置与优化
- ✅ 网络配置和安全组管理
- ✅ 存储、备份策略制定和实施
- ✅ 负载均衡和高可用架构配置

### 3. 容器化与编排
- ✅ Docker容器化应用部署
- ✅ 容器镜像构建与优化
- ✅ 容器编排工具使用（简单版Docker Compose）
- ✅ 容器监控和资源管理
- ✅ 容器安全策略配置

### 4. 数据库运维管理
- ✅ 数据库部署和配置优化
- ✅ 数据库备份与恢复策略
- ✅ 数据库性能监控和调优
- ✅ 数据迁移和版本管理
- ✅ 数据库安全访问控制

### 5. 监控告警与日志管理
- ✅ 应用性能监控(APM)配置
- ✅ 基础设施监控(服务器、网络、存储)
- ✅ 数据库监控与查询性能分析
- ✅ 日志收集、聚合和分析
- ✅ 告警规则制定和响应流程

### 6. 安全运维与合规
- ✅ 系统安全配置和加固
- ✅ SSL证书申请和配置
- ✅ 应用安全扫描与漏洞管理
- ✅ 数据加密和访问控制
- ✅ 安全事件响应和处理

### 7. 性能优化与调优
- ✅ 应用性能监控与瓶颈分析
- ✅ 数据库查询性能优化
- ✅ 静态资源CDN配置与优化
- ✅ 缓存策略配置与管理
- ✅ 应用启动时间和响应时间优化

### 8. 系统备份与灾难恢复
- ✅ 数据备份策略制定与执行
- ✅ 应用配置备份和管理
- ✅ 灾难恢复方案设计和演练
- ✅ 备份数据验证和恢复测试
- ✅ 业务连续性和容灾管理

## 技术栈与工具

### 1. 云服务平台
```bash
# 首选：腾讯云 (推荐给个人开发者)
# 备选：阿里云、华为云

# 推荐配置
服务器规格: 2核4GB内存50GB存储 (约500元/月)
CDN: 基础版 (约20元/月)  
对象存储: OSS/对象存储 (约10元/月)
域名: .com/.cn域名 (约60元/年)
SSL证书: 免费证书
```

### 2. 容器化技术
```dockerfile
# Dockerfile - 后端服务
color-disk/Dockerfile
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 系统依赖
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python依赖
requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

```dockerfile
# Dockerfile - 数据库
color-disk/docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    container_name: xqfc-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://xqfc_user:password@db:5432/xqfc_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app
      - ./logs:/app/logs
    networks:
      - xqfc-network

  db:
    image: postgres:14-alpine
    container_name: xqfc-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=xqfc_db
      - POSTGRES_USER=xqfc_user
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    networks:
      - xqfc-network

  redis:
    image: redis:7-alpine
    container_name: xqfc-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - xqfc-network

  nginx:
    image: nginx:alpine
    container_name: xqfc-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./static:/app/static
    depends_on:
      - app
    networks:
      - xqfc-network

networks:
  xqfc-network:
    driver: bridge

volumes:xqfc:
  postgres_data:
  redis_data:
```

### 3. 监控工具
```yaml
# Prometheus + Grafana 监控配置
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: xqfc-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: xqfc-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: xqfc-node-exporter
    ports:
      - "9100:9100"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

## 部署架构设计

### 1. 单服务器架构（MVP阶段）
```
Internet
    ↓
Domain Name (xqfc.com)
    ↓
DNS ➔ CDN
    ↓
nginx (80/443) ➔ 负载均衡
    ↓
FastAPI (8000)   redis (6379)   postgres (5432)
```

### 2. 基础监控体系
```
Application ➔ Prometheus ➔ Grafana Dashboard
    ↓             ↓
Logs ➜ Fluent Bit ➜ InfluxDB ➜ Granfana Logs

# 关键监控指标
- HTTP请求响应时间
- 数据库查询性能
- 服务器资源使用率
- 错误率和异常监控
- 业务指标监控
```

## 自动化部署

### 1. GitHub Actions CI/CD
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  PYTHON_VERSION: 3.9
  POETRY_VERSION: 1.3

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: ${{ env.POETRY_VERSION }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pypoetry
        key: ${{ runner.os }}-poetry-${{ hashFiles('**/poetry.lock') }}
    
    - name: Install dependencies
      run: |
        poetry config virtualenvs.create false
        poetry install --no-dev
    
    - name: Run tests
      run: |
        poetry run pytest tests/ -v --coverage=./ --coverage-report=xml
      env:
        DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.REGISTRY_URL }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.REGISTRY_URL }}/xqfc-app:latest
          ${{ secrets.REGISTRY_URL }}/xqfc-app:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/xqfc
          docker pull ${{ secrets.REGISTRY_URL }}/xqfc-app:latest
          docker-compose up -d --no-deps app
          docker image prune -f
```

### 2. 部署脚本自动化
```bash
#!/bin/bash
# deploy.sh - 自动化部署脚本

set -e

# 配置变量
APP_NAME="xqfc-app"
IMAGE_TAG="${1:-latest}"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="/opt/xqfc/backup"
LOG_FILE="/opt/xqfc/logs/deploy.log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 数据备份
backup_data() {
    log "开始备份数据库..."
    BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    # 备份PostgreSQL数据库
    docker exec xqfc-db pg_dump -U xqfc_user xqfc_db > "$BACKUP_FILE"
    
    # 保留最近7天的备份
    find "$BACKUP_DIR" -name "db_backup_*.sql" -mtime +7 -delete
    
    log "数据库备份完成: $BACKUP_FILE"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    # 检查应用是否健康
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log "应用健康检查通过"
        return 0
    else
        log "应用健康检查失败"
        return 1
    fi
}

# 优雅停止服务
stop_services() {
    log "正在停止服务..."
    
    # 发送停止信号，等待优雅关闭
    docker-compose stop --timeout=30
    
    # 等待服务完全停止
    sleep 10
    
    log "服务已停止"
}

# 更新服务
update_services() {
    log "更新服务镜像..."
    
    # 拉取新镜像
    docker-compose pull
    
    # 启动新服务
    docker-compose up -d
    
    log "服务已启动，等待服务就绪..."
    
    # 等待服务启动（最大120秒）
    timeout=120
    while [[ $timeout -gt 0 ]]; do
        if health_check; then
            log "服务启动成功"
            return 0
        fi
        sleep 5
        timeout=$((timeout - 5))
    done
    
    log "服务启动超时"
    return 1
}

# 回滚机制
rollback() {
    log "部署失败，开始回滚..."
    
    # 停止当前服务
    docker-compose down
    
    # 回滚到上一个稳定版本
    docker tag xqfc-app:previous xqfc-app:latest
    
    # 重新启动服务
    docker-compose up -d
    
    log "回滚完成"
}

# 主部署流程
main() {
    log "开始部署应用: $APP_NAME"
    
    # 1. 数据备份
    backup_data
    
    # 2. 健康检查（部署前）
    if ! health_check; then
        log "当前服务不健康，不建议进行部署"
        exit 1
    fi
    
    # 3. 停止服务
    stop_services
    
    # 4. 更新服务
    if update_services; then
        log "部署成功"
        
        # 5. 最终健康检查
        sleep 30
        health_check
        
        log "部署流程完成"
    else
        log "部署失败，开始回滚"
        rollback
        exit 1
    fi
}

# 执行主函数
main "$@"
```

## 监控配置

### 1. Prometheus监控配置
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  # 应用监控
  - job_name: 'xqfc-app'
    static_configs:
      - targets: ['app:8000']
    scrape_interval: 10s
    metrics_path: '/metrics'

  # 基础设施监控
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # PostgreSQL监控
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis监控
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Nginx监控
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### 2. 告警规则
```yaml
# prometheus/alert_rules.yml
groups:
  - name: app_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "应用程序错误率过高"
          description: "{{ $labels.instance }} 错误率超过10%"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "接口响应时间过长"
          description: "{{ $labels.instance }} P95响应时间超过1秒"

      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "服务下线"
          description: "{{ $labels.instance }} 服务不可访问"

  - name: infrastructure_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "{{ $labels.instance }} CPU使用率超过80%"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "{{ $labels.instance }} 内存使用率超过85%"

      - alert: DiskSpaceLow
        expr: 100 - ((node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100) > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足"
          description: "{{ $labels.instance }} 磁盘使用率超过90%"
```

## 备份策略

### 1. 数据库备份脚本
```bash
#!/bin/bash
# backup-database.sh - 数据库备份脚本

set -e

# 配置
DB_NAME="xqfc_db"
DB_USER="xqfc_user"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="/opt/xqfc/backup/database"
RETENTION_DAYS=30
S3_BUCKET="xqfc-backups"

# 日期格式
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${DB_NAME}_${DATE}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行 PostgreSQL 备份
echo "开始备份数据库 $DB_NAME..."
sudo -u postgres pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --clean \
    --if-exists \
    --verbose \
    > "$BACKUP_DIR/$BACKUP_FILE"

# 压缩备份文件
echo "压缩备份文件..."
gzip "$BACKUP_DIR/$BACKUP_FILE"

# 上传到对象存储（可选）
if command -v aws &> /dev/null; then
    echo "上传到对象存储..."
    aws s3 cp "$BACKUP_DIR/$COMPRESSED_FILE" "s3://$S3_BUCKET/database/"
fi

# 验证备份文件
if gzip -t "$BACKUP_DIR/$COMPRESSED_FILE"; then
    echo "备份文件验证通过: $COMPRESSED_FILE"
else
    echo "备份文件验证失败!"
    exit 1
fi

# 清理旧备份（本地）
echo "清理超过 $RETENTION_DAYS 天的旧备份..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 清理旧备份（云端）
if command -v aws &> /dev/null; then
    echo "清理云端旧备份..."
    aws s3 ls "s3://$S3_BUCKET/database/" --recursive | \
        awk '{cmd="date -d \"$1\" +%s"; cmd | getline date; close(cmd); if (date < '"$(date -d "$RETENTION_DAYS days ago" +%s)"') print $4}' | \
        while read -r object; do
            aws s3 rm "s3://$S3_BUCKET/$object"
        done
fi

echo "数据库备份完成！"
```

### 2. 系统备份脚本
```bash
#!/bin/bash
# backup-system.sh - 系统配置与应用备份

# 备份应用代码
backup_app() {
    echo "备份应用代码..."
    APP_BACKUP="/opt/xqfc/backup/app/app_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    # 创建应用代码备份（排除日志和缓存）
    tar -czf "$APP_BACKUP" \
        --exclude="*.log" \
        --exclude="__pycache__" \
        --exclude=".git" \
        --exclude="static/uploads" \
        -C /opt/xqfc \
        app/
    
    echo "应用代码备份完成: $APP_BACKUP"
}

# 备份配置文件
backup_configs() {
    echo "备份配置文件..."
    CONFIG_BACKUP="/opt/xqfc/backup/config/config_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    tar -czf "$CONFIG_BACKUP" \
        -C /opt/xqfc \
        docker-compose.yml \
        nginx/ \
        config/
    
    echo "配置文件备份完成: $CONFIG_BACKUP"
}

# 备份SSL证书
backup_ssl() {
    echo "备份SSL证书..."
    SSL_BACKUP="/opt/xqfc/backup/ssl/ssl_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    tar -czf "$SSL_BACKUP" \
        -C /opt/xqfc \
        nginx/ssl/
    
    echo "SSL证书备份完成: $SSL_BACKUP"
}

# 主函数
main() {
    echo "开始系统备份..."
    
    # 创建备份目录
    mkdir -p /opt/xqfc/backup/{app,config,ssl}
    
    # 执行备份
    backup_app
    backup_configs
    backup_ssl
    
    echo "系统备份完成！"
}

main "$@"
```

---

**文档说明**: 本DevOps工程师角色定义涵盖自动化部署、云服务器管理、监控告警和备份恢复等运维工作。对于个人开发者项目采用轻量级、成本效益最高的方案。AI可以协助自动化脚本生成、部署配置和故障排查，特别适合单人开发环境。后续根据项目规模发展可升级到更复杂的云原生架构。注重自动化、可靠性和成本控制的平衡。DevOps角色确保即使单人开发也能保持专业级别的运维标准。