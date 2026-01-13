# 部署检查清单

## 服务器准备阶段

- [ ] 确认服务器配置：CentOS 7.9, 2核2G
- [ ] 确认公网IP：8.138.129.142
- [ ] 安装宝塔面板
- [ ] 在宝塔面板安装软件：
  - [ ] Nginx 1.20+
  - [ ] MySQL 5.7+
  - [ ] Redis 6.0+
  - [ ] Python 3.8+
  - [ ] Supervisor

## 数据库配置

- [ ] 在宝塔面板创建数据库 `xqfc_db`
- [ ] 创建数据库用户 `xqfc_user`
- [ ] 设置强密码并保存
- [ ] 字符集选择 `utf8mb4`

## 代码部署

- [ ] 创建项目目录 `/www/wwwroot/county-real-estate`
- [ ] 上传 `backend` 目录到服务器
- [ ] 确认 `requirements.txt` 文件存在

## Python环境

- [ ] 创建Python虚拟环境
- [ ] 激活虚拟环境
- [ ] 升级pip到最新版本
- [ ] 安装项目依赖：`pip install -r requirements.txt`

## 配置文件

- [ ] 创建 `.env` 配置文件
- [ ] 配置数据库连接信息
- [ ] 配置Redis连接信息
- [ ] 生成并设置 `SECRET_KEY`
- [ ] 配置CORS允许的域名
- [ ] 配置上传文件目录路径

## 数据库初始化

- [ ] 运行数据库迁移脚本
- [ ] 确认数据表创建成功
- [ ] 检查数据库表结构

## Nginx配置

- [ ] 在宝塔面板添加站点
- [ ] 配置域名/IP：8.138.129.142
- [ ] 添加反向代理配置 `/api/`
- [ ] 配置静态文件路径 `/static/`
- [ ] 测试Nginx配置
- [ ] 重载Nginx配置

## Supervisor配置

- [ ] 添加Supervisor守护进程
- [ ] 配置进程名称：`county_real_estate`
- [ ] 配置启动命令
- [ ] 设置自动启动
- [ ] 启动进程

## 防火墙配置

- [ ] 宝塔面板安全放行端口：80、443
- [ ] 阿里云安全组放行端口：80、443
- [ ] （可选）放行8000端口用于直接访问后端

## 部署验证

- [ ] 检查服务状态：`supervisorctl status county_real_estate`
- [ ] 查看应用日志：`tail -f logs/app.log`
- [ ] 测试健康检查：`curl http://8.138.129.142/health`
- [ ] 访问API文档：`http://8.138.129.142/docs`
- [ ] 测试API端点响应

## 微信小程序配置（后续）

- [ ] 注册微信小程序账号
- [ ] 获取 AppID 和 AppSecret
- [ ] 更新 `.env` 文件中的微信配置
- [ ] 在小程序后台配置服务器域名
- [ ] 上传小程序代码并提交审核

## HTTPS配置（可选但推荐）

- [ ] 在宝塔面板申请SSL证书
- [ ] 启用HTTPS强制跳转
- [ ] 更新小程序服务器域名配置为HTTPS

## 备份策略

- [ ] 设置数据库自动备份
- [ ] 设置定期文件备份
- [ ] 测试恢复流程

## 监控和日志

- [ ] 配置日志轮转
- [ ] 设置磁盘空间监控
- [ ] 配置服务异常告警

---

## 快速参考信息

```
服务器IP: 8.138.129.142
项目目录: /www/wwwroot/county-real-estate
后端目录: /www/wwwroot/county-real-estate/backend
虚拟环境: /www/wwwroot/county-real-estate/venv
日志目录: /www/wwwroot/county-real-estate/logs
上传目录: /www/wwwroot/county-real-estate/uploads

数据库名: xqfc_db
数据库用户: xqfc_user
数据库端口: 3306

Redis端口: 6379
后端端口: 8000
Nginx端口: 80/443
```

## 常用命令

```bash
# 查看服务状态
supervisorctl status county_real_estate

# 重启服务
supervisorctl restart county_real_estate

# 查看实时日志
tail -f /www/wwwroot/county-real-estate/logs/app.log

# 查看Nginx日志
tail -f /www/wwwlogs/county_real_estate_access.log
tail -f /www/wwwlogs/county_real_estate_error.log
```
